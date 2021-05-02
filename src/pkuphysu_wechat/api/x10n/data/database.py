from sqlalchemy.sql.expression import func

from pkuphysu_wechat import db


class Datax10nProbs(db.Model):
    __tablename__ = "x10nProbs"

    probid = db.Column(db.String(32), primary_key=True)
    text = db.Column(db.Unicode(32), nullable=False)
    img = db.Column(db.String(64), nullable=False)
    choices = db.Column(db.String(64), nullable=False)
    answer = db.Column(db.String(16), nullable=False)

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
            problem.choices = "|".join([str(x) for x in prob["choices"]])
            problem.answer = prob["answer"]
        else:
            problem = cls(
                probid=prob["probid"],
                text=prob["text"],
                img=prob["img"],
                choices="|".join([str(x) for x in prob["choices"]]),
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
            "choices": prob.choices.split("|"),
        }
        return problem

    @classmethod
    def get_ran_probids(cls, number) -> list:
        assert isinstance(number, int) and number >= 1, "不合法的数字输入"
        # need testing
        return [
            db.session.query(cls).order_by(func.random()).first().probid
            for x in range(number)
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
