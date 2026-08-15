from sqlalchemy.exc import IntegrityError

from pkuphysu_wechat import db


class SituationPuzzleTurnPending(RuntimeError):
    pass


class PuzzleUnlock(db.Model):
    __tablename__ = "PuzzleUnlock"
    id = db.Column(db.Integer, primary_key=True)
    open_id = db.Column(db.String(32), nullable=False)
    dependence_unlocked = db.Column(db.String(16), nullable=False)

    @classmethod
    def clear(cls):  # 清空
        all_cols = cls.query.all()
        for col in all_cols:
            db.session.delete(db.session.get(cls, col.id))
        db.session.commit()

    @classmethod  # 一个一个加入
    def add(cls, openid: str, dependence_unlocked: str):
        col = cls(open_id=openid, dependence_unlocked=dependence_unlocked)
        db.session.add(col)
        db.session.commit()

    @classmethod
    def check(cls, openid: str, dependence_unlocked: str):
        return (
            cls.query.filter(
                cls.open_id == openid and cls.dependence_unlocked == dependence_unlocked
            ).first()
            is not None
        )

    @classmethod
    def clear_personal_information(cls, openid: str):
        lst = cls.query.filter_by(open_id=openid).all()
        for record in lst:
            db.session.delete(db.session.get(cls, record.id))
        db.session.commit()


class SituationPuzzleState(db.Model):
    """Database-backed global state for the currently selected puzzle."""

    __tablename__ = "SituationPuzzleState"

    id = db.Column(db.Integer, primary_key=True)
    active_puzzle_id = db.Column(db.String(16), nullable=False)

    @classmethod
    def get_active_puzzle_id(cls):
        state = db.session.get(cls, 1)
        if state is None:
            state = cls(id=1, active_puzzle_id="1")
            db.session.add(state)
            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()
                state = db.session.get(cls, 1)
        return state.active_puzzle_id

    @classmethod
    def set_active_puzzle_id(cls, puzzle_id):
        state = db.session.get(cls, 1)
        if state is None:
            state = cls(id=1, active_puzzle_id=puzzle_id)
        else:
            state.active_puzzle_id = puzzle_id
        db.session.add(state)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            state = db.session.get(cls, 1)
            state.active_puzzle_id = puzzle_id
            db.session.commit()


class SituationPuzzleConversation(db.Model):
    """The durable generation and sequence allocator for one player's puzzle."""

    __tablename__ = "SituationPuzzleConversation"
    __table_args__ = (
        db.UniqueConstraint(
            "open_id", "puzzle_id", name="uq_situation_puzzle_conversation"
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    open_id = db.Column(db.String(64), nullable=False)
    puzzle_id = db.Column(db.String(16), nullable=False)
    generation = db.Column(db.Integer, nullable=False, default=1)
    next_sequence = db.Column(db.Integer, nullable=False, default=1)

    @classmethod
    def get_or_create(cls, open_id, puzzle_id):
        conversation = cls.query.filter_by(open_id=open_id, puzzle_id=puzzle_id).first()
        if conversation is not None:
            return conversation

        conversation = cls(open_id=open_id, puzzle_id=puzzle_id)
        db.session.add(conversation)
        try:
            db.session.commit()
            return conversation
        except IntegrityError:
            db.session.rollback()
            return cls.query.filter_by(open_id=open_id, puzzle_id=puzzle_id).one()

    @classmethod
    def reset(cls, open_id, puzzle_id):
        conversation = cls.get_or_create(open_id, puzzle_id)
        conversation = cls.query.filter_by(id=conversation.id).with_for_update().one()
        conversation.generation += 1
        conversation.next_sequence = 1
        db.session.commit()


class SituationPuzzleTurn(db.Model):
    """A durable user/assistant turn with explicit completion state."""

    __tablename__ = "SituationPuzzleTurn"
    __table_args__ = (
        db.UniqueConstraint(
            "conversation_id",
            "generation",
            "sequence",
            name="uq_situation_puzzle_turn_order",
        ),
        db.Index(
            "ix_situation_puzzle_turn_history",
            "conversation_id",
            "generation",
            "status",
            "sequence",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(
        db.Integer,
        db.ForeignKey("SituationPuzzleConversation.id"),
        nullable=False,
    )
    generation = db.Column(db.Integer, nullable=False)
    sequence = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(16), nullable=False)
    user_content = db.Column(db.Text, nullable=False)
    assistant_content = db.Column(db.Text)
    created_at = db.Column(db.DateTime, nullable=False, server_default=db.func.now())

    @classmethod
    def begin(cls, open_id, puzzle_id, user_content):
        conversation = SituationPuzzleConversation.get_or_create(open_id, puzzle_id)
        conversation = (
            SituationPuzzleConversation.query.filter_by(id=conversation.id)
            .with_for_update()
            .one()
        )
        pending_turn = cls.query.filter_by(
            conversation_id=conversation.id,
            generation=conversation.generation,
            status="pending",
        ).first()
        if pending_turn is not None:
            db.session.rollback()
            raise SituationPuzzleTurnPending(
                "A situation-puzzle turn is already pending"
            )
        turn = cls(
            conversation_id=conversation.id,
            generation=conversation.generation,
            sequence=conversation.next_sequence,
            status="pending",
            user_content=user_content,
        )
        conversation.next_sequence += 1
        db.session.add(turn)
        db.session.commit()
        return turn

    @classmethod
    def messages_for(cls, turn, limit):
        completed_turns = (
            cls.query.filter(
                cls.conversation_id == turn.conversation_id,
                cls.generation == turn.generation,
                cls.status == "completed",
                cls.sequence < turn.sequence,
            )
            .order_by(cls.sequence.desc())
            .limit(limit)
            .all()
        )
        messages = []
        for completed_turn in reversed(completed_turns):
            messages.extend(
                [
                    {"role": "user", "content": completed_turn.user_content},
                    {
                        "role": "assistant",
                        "content": completed_turn.assistant_content,
                    },
                ]
            )
        messages.append({"role": "user", "content": turn.user_content})
        return messages

    @classmethod
    def complete(cls, turn_id, assistant_content):
        turn = cls.query.filter_by(id=turn_id).with_for_update().one()
        conversation = (
            SituationPuzzleConversation.query.filter_by(id=turn.conversation_id)
            .with_for_update()
            .one()
        )
        if turn.status != "pending" or turn.generation != conversation.generation:
            turn.status = "stale"
            db.session.commit()
            return False
        turn.status = "completed"
        turn.assistant_content = assistant_content
        db.session.commit()
        return True

    @classmethod
    def fail(cls, turn_id):
        turn = cls.query.filter_by(id=turn_id).with_for_update().first()
        if turn is not None and turn.status == "pending":
            turn.status = "failed"
        db.session.commit()


class PuzzleReview(db.Model):
    __tablename__ = "PuzzleReview"
    id = db.Column(db.Integer, primary_key=True)
    open_id = db.Column(db.String(32), nullable=False)
    review = db.Column(db.Unicode(256), nullable=False)

    @classmethod
    def add(cls, openid: str, payload: str):
        col = cls(open_id=openid, review=payload)
        db.session.add(col)
        db.session.commit()
