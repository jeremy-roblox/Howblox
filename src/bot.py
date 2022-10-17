from os import environ
import asyncio
import logging
import signal 
import os 
from resources.constants import MODULE_DIR # pylint: disable=import-error, no-name-im-module
from resources.structures.Howblox import Howblox # pylint: disable=import-error, no-name-im-module
from resources.secrets import TOKEN # , SENTRY_URL, VALID_SECRETS # pylint: disable=import-error, no-name-in-module

logger = logging.getLogger()
logging.basicConfig(level=getattr(logging, environ.get("LOG_LEVEL", "WARNING")))



async def register_modules():
    get_files = Howblox.get_module("utils", attrs="get_files")

    for directory in MODULE_DIR: # pylint: disable=E1101
        files = get_files(directory)

        for filename in [f.replace(".py","") for f in files]:
            Howblox.get_module(path=directory, dir_name=filename)

"""
def load_sentry():
    from resources.constants import RELEASE # pylint: disable=import-error, no-name-in-module

    if RELEASE != "LOCAL":
        try:
            import sentry_sdk

            sentry_sdk.set_tag("release", RELEASE)

            def strip_sensitive_data(event, hint):
                print(event, flush=True)

                for i, value in enumerate(event.get("threads", {}).get("values", [])):
                    for ii, frame in enumerate(value.get("stacktrace", {}).get("frames", [])):
                        for env_var_name, _ in frame.get("environ", {}).items():
                            if env_var_name in VALID_SECRETS:
                                frame["environ"][env_var_name] = "REDACTED"

                                event["threads"]["values"][i]["stacktrace"]["frames"][ii] = frame
                                print("found a yikes", flush=True)


                return event

            sentry_sdk.init(
                SENTRY_URL, traces_sample_rate=1.0, before_send=strip_sensitive_data
            )

        except:
            print("sentry failed", flush=True)
"""


async def handle_signal(sig):
    """handle the Unix SIGINT and SIGTERM signals.
        `SystemExit's are incorrectly caught, so we have to use 
        os._exit until this is fixed"""

    Howblox.log(f"Handling signal {sig}")

    loop = asyncio.get_event_loop()

    await Howblox.close()

    loop.stop()

    for task in asyncio.all_tasks():
        task.cancel()

    os._exit(0)
    #sys.exit(0)

async def signals_handler():
    loop = asyncio.get_event_loop()

    for signame in ("SIGINT", "SIGTERM"):
        loop.add_signal_handler(getattr(signal, signame),
                                lambda: asyncio.ensure_future(handle_signal(signame), loop=loop))

async def main():
    #load_sentry()

    await signals_handler()
    await register_modules()

    async with Howblox as bot:
        await bot.start(TOKEN)



if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    asyncio.set_event_loop(loop)

    try:
        loop.run_until_complete(main())
    finally:
        loop.run_until_complete(Howblox.close())
        loop.close()