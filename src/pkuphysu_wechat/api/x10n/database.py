from pkuphysu_wechat import db


class Datax10n(db.Model):
    __tablename__ = "x10n"
    openid = db.Column(db.String(32), primary_key=True)
    result = db.Column(db.String(1024))

    @classmethod
    def get_info(cls, openid: str) -> dict:
        student = cls.query.get(openid)
        if student is None:
            student = cls(openid=openid)
            db.session.add(student)
            db.session.commit()
            return {"played": False}
        return {"played": True, "result": student.result}

    @classmethod
    def put_info(cls, openid: str, result: str) -> bool:
        student = cls.query.get(openid)
        if student is None or student.result:
            return False
        student.result = result
        db.session.add(student)
        db.session.commit()
        return True

    @classmethod
    def del_info(cls, openid: str) -> bool:
        "For debug only"
        student = cls.query.get(openid)
        db.session.delete(student)
        db.session.commit()
