import json

from sqlalchemy.sql.expression import func

from pkuphysu_wechat import db


class Datax10nProbs(db.Model):
    __tablename__ = "x10nProbs"

    probid = db.Column(db.String(4), primary_key=True)
    text = db.Column(db.String(256), nullable=False)
    img = db.Column(db.String(256), nullable=False)
    choices = db.Column(db.String(256), nullable=False)
    answer = db.Column(db.String(1), nullable=False)

    @classmethod
    def put_prob(cls, prob: dict) -> None:
        assert len(prob) == 4, "不合法的题目形式"
        assert (
            isinstance(prob["probid"], str)
            and isinstance(prob["text"], str)
            and isinstance(prob["img"], str)
            and isinstance(prob["answer"], str)
        ), "题目前三项应为字符串"
        assert isinstance(prob["choices"], list), "题目选项应为列表"
        problem = cls.query.get(prob["probid"])
        if problem:
            print(f"覆盖第{prob['probid']}题")
            problem.text = prob["text"]
            problem.img = prob["img"]
            problem.choices = json.dumps([str(x) for x in prob["choices"]])
            problem.answer = prob["answer"]
        else:
            problem = cls(
                probid=prob["probid"],
                text=prob["text"],
                img=prob["img"],
                choices=json.dumps([str(x) for x in prob["choices"]]),
                answer=prob["answer"],
            )
        db.session.add(problem)
        db.session.commit()

    @classmethod
    def get_prob(cls, probid: str) -> dict:
        assert isinstance(probid, str), "不合法的id输入"
        prob = cls.query.get(probid)
        problem = {
            "text": prob.text,
            "img": prob.img,
            "choices": json.loads(prob.choices),
        }
        return problem

    @classmethod
    def get_ran_probids(cls, number) -> list:
        assert isinstance(number, int) and number >= 1, "不合法的数字输入"
        return [
            x.probid
            for x in db.session.query(cls).order_by(func.random()).limit(number)
        ]

    @classmethod
    def get_ans(cls, probid: str) -> list:
        assert isinstance(probid, str), "不合法的id输入"
        prob = cls.query.get(probid)
        return prob.answer

    @classmethod
    def del_prob(cls, probid: str) -> None:
        assert isinstance(probid, str), "不合法的id输入"
        prob = cls.query.get(probid)
        db.session.delete(prob)
        db.session.commit()
