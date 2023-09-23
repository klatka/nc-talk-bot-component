# Nextcloud Talk - Bot Messages
[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg?style=for-the-badge)](https://github.com/hacs/integration)

Custom component for Home Assistant to publish messages from Home Assistant to a room in Nextcloud Talk.

## Requirements
- Nextcloud >= 27.1
- Nextcloud Talk >= 17.1

## Install

1. Create a bot in Nextcloud Talk (see [nextcloud docs](https://nextcloud-talk.readthedocs.io/en/latest/bots/)):

    Use [occ](https://docs.nextcloud.com/server/latest/admin_manual/configuration_server/occ_command.html) to create a new bot:
    ```shell
    occ talk:bot:install "<name>" "<shared_secret>" "<webhook_url>"
    ```
    Get the id of the created bot:
    ```shell
    occ talk:bot:list
    ```
    Create a room in Nextcloud Talk (you get the room token within the response):
    ```shell
    occ talk:room:create --user <your_uid> --owner <your_uid> <room_name>
    ```
    Assign bot to this room:
    ```shell
    occ talk:bot:setup <bot_id> <room_token>
    ```

2. Install this component in Home Assistant:

    Add this repository to HACS
    Install nctalkbot in HACS
    Restart Home Assistant
    Add this to your `configuration.yaml`:
    ```yaml
    notify:
      - platform: nctalkbot
        name: nctalkbot
        url: !secret nextcloud_url
        shared_secret: !secret nextcloud_talk_shared_secret
        room_token: !secret nextcloud_talk_room_token
    ```
    Add needed secrets in your `secrets.yaml`
    Restart Home Assistant again

## Usage

Use service `notify.nctalkbot`:
```yaml
service: notify.nctalkbot
data:
  message: Test from Home Assistant
```

If you want to target another room, you can set the room token like this:
```yaml
service: notify.nctalkbot
data:
  message: Test from Home Assistant
  target: <room-token>
```
Note: The bot must be assigned to your target room!


<a href="https://www.buymeacoffee.com/klatka" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/default-orange.png" alt="Buy Me a Coffee" height="41" width="174"></a>
