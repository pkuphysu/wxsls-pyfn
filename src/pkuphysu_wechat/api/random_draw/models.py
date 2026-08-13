from pkuphysu_wechat import db


class RandomDraw(db.Model):
    __tablename__ = "RandomDraw"

    openid = db.Column(db.String(32), primary_key=True)
    name = db.Column(db.String(16), nullable=False)

    @classmethod
    def add_participant(cls, openid: str, name: str) -> bool:
        if db.session.get(cls, openid):
            return False
        db.session.add(cls(openid=openid, name=name))
        db.session.commit()
        return True
