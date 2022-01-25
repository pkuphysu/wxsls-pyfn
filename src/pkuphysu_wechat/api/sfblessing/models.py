from typing import Optional

from sqlalchemy.sql import func

from pkuphysu_wechat import db

from . import simple_cipher


def format_message(from_id, content):
    name = simple_cipher.encode_name(SFBlessing.get_first_bless_id_by(from_id))
    return f"[{name}] {content}"


class SFBlessing(db.Model):
    __tablename__ = "SFBlessing"
    blessing_id = db.Column(db.Integer, primary_key=True)
    create_time = db.Column(db.DateTime, server_default=func.now())
    create_by = db.Column(db.String(32), nullable=False)
    content = db.Column(db.Unicode(256))

    @classmethod
    def add_bless(cls, create_by, content):  # 将祝福数据保存在数据库中
        if not BlessBan.is_name_baned(create_by):
            bless_record = cls(create_by=create_by, content=content)
            db.session.add(bless_record)
            db.session.commit()
            return bless_record

    @classmethod
    def get_by_date(cls, date):
        "将某一天的祝福数据全部提取出来"
        return cls.query.filter(func.date(cls.create_time) == date).all()

    @classmethod
    def remove_bless(cls, person=None, blessing_id=None):  # 删除某一个id或某一个人的祝福
        if blessing_id is not None:
            db.session.delete(cls.query.get(blessing_id))
        if person is not None:
            ban_lst = cls.query.filter_by(create_by=person).all()
            for ban_record in ban_lst:
                db.session.delete(cls.query.get(ban_record.blessing_id))
        db.session.commit()

    @classmethod
    def get_first_bless_id_by(cls, create_by: str) -> Optional[int]:
        record = cls.query.filter_by(create_by=create_by).first()
        if record is None:
            return None
        return record.blessing_id

    @classmethod
    def undo_bless(cls, create_by: str) -> Optional[str]:
        "删除用户最后一句祝福，返回其文本"
        record = (
            cls.query.filter_by(create_by=create_by)
            .order_by(cls.create_time.desc())
            .first()
        )
        if record is None:
            return None
        db.session.delete(record)
        db.session.commit()
        return record.content

    @classmethod
    def get_creator(cls, blessing_id: int) -> Optional[str]:
        record = cls.query.get(blessing_id)
        if record is None:
            return None
        return record.create_by


class SFBackBlessing(db.Model):  # 和上面基本一致，多了一个send_to，即向谁发送的列
    __tablename__ = "SFBackBlessing"
    backblessing_id = db.Column(db.Integer, primary_key=True)
    create_time = db.Column(db.DateTime, server_default=func.now())
    create_by = db.Column(db.String(32), nullable=False)
    send_to = db.Column(db.String(32), nullable=False)
    content = db.Column(db.Unicode(256))

    @classmethod
    def add_backbless(cls, create_by, send_to, content):
        if not BlessBan.is_name_baned(create_by):
            bless_record = cls(create_by=create_by, send_to=send_to, content=content)
            db.session.add(bless_record)
            db.session.commit()

    @classmethod
    def get_backbless_to(cls, person):
        return cls.query.filter_by(send_to=person).all()

    @classmethod
    def get_by_date(cls, date):
        "将某一天的祝福数据全部提取出来"
        return cls.query.filter(func.date(cls.create_time) == date).all()

    @classmethod
    def remove_backbless(cls, person=None, backblessing_id=None):
        if backblessing_id is not None:
            db.session.delete(cls.query.get(backblessing_id))
        if person is not None:
            ban_lst = cls.query.filter_by(create_by=person).all()
            for ban_record in ban_lst:
                db.session.delete(cls.query.get(ban_record.backblessing_id))
        db.session.commit()


class BlessBan(db.Model):  # 存储禁掉的人的数据
    __tablename__ = "BlessBan"
    bless_id = db.Column(db.String(32), primary_key=True)

    @classmethod
    def add_name(cls, bless_id):  # 添加
        if not cls.is_name_baned(bless_id):
            db.session.add(cls(bless_id=bless_id))
            db.session.commit()

    @classmethod
    def remove_name(cls, bless_id):  # 移除
        if cls.is_name_baned(bless_id):
            db.session.delete(cls.query.get(bless_id))
            db.session.commit()

    @classmethod
    def is_name_baned(cls, bless_id):
        return cls.query.filter(cls.bless_id == bless_id).first() is not None
