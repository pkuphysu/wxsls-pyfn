from pkuphysu_wechat import db


class PuzzleUnlock(db.Model):
    __tablename__ = "PuzzleUnlock"
    id = db.Column(db.Integer, primary_key=True)
    open_id = db.Column(db.String(32), nullable=False)
    dependence_unlocked = db.Column(db.String(16), nullable=False)

    @classmethod
    def clear(cls):  # 清空
        all_cols = cls.query.all()
        for col in all_cols:
            db.session.delete(cls.query.get(col.id))
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
            db.session.delete(cls.query.get(record.id))
        db.session.commit()
