from pkuphysu_wechat import db


class Puzzle(db.Model):  # 存储当前谜语
    __tablename__ = "Puzzle"
    id = db.Column(db.Integer, primary_key=True)
    line_type = db.Column(db.String(32), nullable=False)
    # type分为"cover","questions","answer","explanation","clue","keyword"六种
    keyword = db.Column(db.String(32))
    # 如果是"cover","questions","answers"，"explanation"留空，"clue","keyword"为关键词，例：皮特
    ques_id = db.Column(db.String(32))
    # 如果是"cover","questions","answers"，"explanation"留空，"clue","keyword"为问题字母，例：A
    content = db.Column(db.String(256), nullable=False)
    # 如果是"cover","questions","answers" "explanation"就是内容；如果是"keyword"则为某问题题面；
    # 如果是"clue"则是某问题答案
    locked = db.Column(db.String(1), nullable=False)
    # 是否默认锁住，"T"or"F"

    @classmethod
    def clear(cls):  # 清空
        all_cols = cls.query.all()
        for col in all_cols:
            db.session.delete(cls.query.get(col.id))
        db.session.commit()

    @classmethod
    def put_in(cls, puzzle: dict):  # 加入
        cover = cls(line_type="cover", content=puzzle["cover"], locked="F")
        db.session.add(cover)
        questions = cls(line_type="questions", content=puzzle["questions"], locked="F")
        db.session.add(questions)
        answers = cls(line_type="answers", content=puzzle["answers"], locked="F")
        db.session.add(answers)
        explanation = cls(
            line_type="explanation", content=puzzle["explanation"], locked="F"
        )
        db.session.add(explanation)

        keywords = puzzle["keywords"]
        for keyword, v in keywords.items():
            for ques_id, value in v.items():
                column = cls(
                    line_type="keyword",
                    keyword=keyword,
                    ques_id=ques_id,
                    content=value,
                    locked="F",
                )
                db.session.add(column)

        clues = puzzle["clue"]
        for keyword, v in clues.items():
            for ques_id, value in v.items():
                column = cls(
                    line_type="clue",
                    keyword=keyword,
                    ques_id=ques_id,
                    content=value,
                    locked="F",
                )
                db.session.add(column)

        db.session.commit()

    @classmethod
    def get_cover(cls) -> str:
        cover = cls.query.filter_by(line_type="cover").first()
        if cover is None:
            return None
        return cover.content

    @classmethod
    def get_questions(cls) -> str:
        questions = cls.query.filter_by(line_type="questions").first()
        if questions is None:
            return None
        return questions.content

    @classmethod
    def get_answers(cls) -> str:
        answers = cls.query.filter_by(line_type="answers").first()
        if answers is None:
            return None
        return answers.content

    @classmethod
    def get_explanation(cls) -> str:
        explanation = cls.query.filter_by(line_type="explanation").first()
        if explanation is None:
            return None
        return explanation.content

    @classmethod
    def alter_default_status(cls, keyword: str):
        columns = cls.query.filter(
            cls.line_type == "keyword" and cls.keyword == keyword
        ).all()
        for col in columns:
            col.locked = "T"
            db.session.add(col)
        db.session.commit()

    @classmethod
    def get_locked(cls, keyword: str) -> bool:
        """返回某关键词是否默认上锁"""
        column = cls.query.filter(
            cls.line_type == "keyword" and cls.keyword == keyword
        ).first()
        return column.locked == "T"

    @classmethod
    def get_keyword(cls):
        column=cls.query.filter(
        cls.line_type=="keyword"
            and cls.ques_id=="A"
        ).all()
        li=[]
        for i in column:
            li.append(i.keyword)
        return li
    # 所有不重复的默认不锁的关键词和默认锁的

    @classmethod
    def get_keyquestions(cls,keyword:str):
        column=cls.query.filter(
        cls.line_type=="keyword"
            and cls.keyword==keyword
        ).all()
        li=[]
        for i in column:
            li.append("%s %s:%s",%(keyword,i.ques_id,i.content))
        return li

    @classmethod
    def get_clue(cls, keyword: str, ques_id: str) -> str:
        """
        拿关键词(keyword)和问题代码(ques_id,应该是[ABCD]的形式）换答案
        """
        column = cls.query.filter(
            cls.line_type == "clue"
            and cls.keyword == keyword
            and cls.ques_id == ques_id
        ).first()
        return column.content


class PuzzleDependence(db.Model):  # 存储当前谜语之间依赖
    __tablename__ = "PuzzleDependence"
    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.String(32), nullable=False)
    keyword = db.Column(db.String(32), nullable=False)

    @classmethod
    def clear(cls):  # 清空
        all_cols = cls.query.all()
        for col in all_cols:
            db.session.delete(cls.query.get(col.id))
        db.session.commit()

    @classmethod
    def put_in(cls, dependence: dict):  # 加入
        for k, v in dependence.items():
            column = cls(question=k, keyword=v)
            db.session.add(column)
            Puzzle.alter_default_status(v)
        db.session.commit()
    @classmethod
    def get_Kid(cls,keyword):
        column=cls.query.filter(
        cls.keyword==keyword
        ).first()
        return column.id
    @classmethod
    def get_Qid(cls,question):
        column=cls.query.filter(
        cls.question==question
        ).first()
        return column.id

