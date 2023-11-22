from os import getenv


def init_debugger(app):
    if getenv("DEBUGGER") == "True":
        print("⏳ Will Set Up Debugger!⏳ ", flush=True)

        import debugpy

        # Set these flags forced for flask so reloader does not happen
        app.config["ENV"] = "production"
        app.config["DEBUG"] = False

        debugpy.listen(("0.0.0.0", 5678))
        print("⏳ VS Code debugger can now be attached, press F5 in VS Code ⏳", flush=True)
        debugpy.wait_for_client()
        print("🎉 VS Code debugger attached, enjoy debugging 🎉", flush=True)
