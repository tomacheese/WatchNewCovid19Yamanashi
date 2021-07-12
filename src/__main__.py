import re
from datetime import datetime, timezone

from src import load_notified_ids, send_to_discord, add_notified_id, config, logger
from src.Covid19Yamanashi import get_all_corona_list_pages


def main():
    notified_ids = load_notified_ids()
    isFirst = len(notified_ids) == 0

    items = get_all_corona_list_pages()
    fields = []
    nums = {}
    for o in items.values():
        for item in o.values():
            title = item["title"]
            num = item["num"]

            if title in notified_ids:
                continue

            logger.info(title, num)
            logger.info(item)
            htmls = item["htmls"]
            htmls = list(map(lambda x: re.sub(r"<b>(.+)</b>", "**\\1**", x), htmls))
            htmls = list(map(lambda x: re.sub(r"<u>(.+)</u>", "__\\1__", x), htmls))
            htmls = list(map(lambda x: re.sub(r"<[^>]*?>", "", x), htmls))
            print("\n".join(htmls))

            fields.append({
                "name": (":new:" if num == "1" else ":up:") + title,
                "value": "\n".join(htmls)
            })
            if num not in nums:
                nums[num] = 0
            nums[num] += 1

            if not isFirst and len(fields) >= 25:
                embed = {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "fields": fields
                }
                send_to_discord(config.DISCORD_TOKEN, config.DISCORD_CHANNEL_ID, "", embed)
            add_notified_id(title)

    if not isFirst and len(fields) > 0:
        embed = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "fields": fields
        }
        send_to_discord(config.DISCORD_TOKEN, config.DISCORD_CHANNEL_ID, "", embed)

    if not isFirst and len(nums.keys()) > 0:
        send_to_discord(
            config.DISCORD_TOKEN,
            config.DISCORD_CHANNEL_ID,
            "計:\n" + "\n".join(list(map(lambda x: "・第" + str(x[0]) + "報: " + str(x[1]) + "個", nums.items())))
        )


if __name__ == "__main__":
    main()
