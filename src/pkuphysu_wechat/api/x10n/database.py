import json

from pkuphysu_wechat import db


class Datax10n(db.Model):
    __tablename__ = "x10nUser"
    openid = db.Column(db.String(32), primary_key=True)
    result = db.Column(db.String(4096))
    starttime = db.Column(db.String(64))
    prob_ids = db.Column(db.String(512))
    name = db.Column(db.String(32))
    stu_id = db.Column(db.String(32))

    @classmethod
    def get_info(cls, openid: str) -> dict:
        student = cls.query.get(openid)
        if student is None:
            student = cls(openid=openid)
            db.session.add(student)
            db.session.commit()
            return {"played": False}
        return {
            "played": True,
            "result": None if student.result is None else json.loads(student.result),
        }

    @classmethod
    def startgame(cls, openid: str, starttime: str, prob_ids: list) -> bool:
        student = cls.query.get(openid)
        if student is None:
            return False
        else:
            student.starttime = starttime
            student.prob_ids = json.dumps(prob_ids)
            db.session.add(student)
            db.session.commit()
            return True

    @classmethod
    def get_probs(cls, openid: str) -> list:
        student = cls.query.get(openid)
        assert student is not None, "用户不存在"
        prob_ids = json.loads(student.prob_ids)
        return prob_ids

    @classmethod
    def get_starttime(cls, openid: str) -> float:
        student = cls.query.get(openid)
        assert student is not None, "用户不存在"
        start_time = float(student.starttime)
        return start_time

    @classmethod
    def put_name(cls, openid: str, name: str, stu_id: str) -> bool:
        student = cls.query.get(openid)
        assert student is not None, "用户不存在"
        student.name = name
        student.stu_id = stu_id
        db.session.add(student)
        db.session.commit()
        return True

    @classmethod
    def put_info(cls, openid: str, result: dict) -> bool:
        student = cls.query.get(openid)
        if student is None or student.result:
            return False
        student.result = json.dumps(result)
        db.session.add(student)
        db.session.commit()
        return True

    @classmethod
    def del_info(cls, openid: str) -> bool:
        "For debug only"
        student = cls.query.get(openid)
        db.session.delete(student)
        db.session.commit()
