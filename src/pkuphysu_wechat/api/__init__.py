from importlib import import_module

modules = ["random_draw", "eveparty", "sfblessing", "situation_puzzle"]


def init_app(app):
    for module in modules:
        app.register_blueprint(
            import_module("." + module, package="pkuphysu_wechat.api").bp
        )
