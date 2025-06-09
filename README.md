# wrist_mouse

Scripts for using the [doublepoint touch_sdk](https://github.com/doublepointlab/touch-sdk-py) and [WowMouse](https://play.google.com/store/apps/details?id=io.port6.watchbridge&pcampaignid=web_share)
in tandem with a keyboard layer as a mouse substitute.


* The main tracking script is standalone in `wrist_mouse_tracker.py`, which polls state from `~/.config/wrist_mouse/tracking_state` for decoupling
* `wrist_mouse_config.py toggle|set OFF|HAND_UP` will write the mode to 
* The talon integration piece is in wrist_mouse_toggler.py

NOTE: you have to activate the defy first
```json
{
    "description": "Toggle wrist_mouse state via dygma macros",
    "manipulators": [
        {
            "type": "basic",
            "from": { "key_code": "f20" },
            "to": [
              {
                "shell_command": "/usr/local/bin/python3 /Users/mjr/.talon/user/wrist_mouse/wrist_mouse_config.py set HAND_UP"
              },
              {
                "set_notification_message": {
                  "id": "wrist_mouse_tracking",
                  "text": "wrist mouse tracking"
                }
              }
            ]
        },
        {
            "type": "basic",
            "from": { "key_code": "f19" },
            "to": [
              {
                "shell_command": "/usr/local/bin/python3 /Users/mjr/.talon/user/wrist_mouse/wrist_mouse_config.py set OFF"
              },
              {
                "set_notification_message": {
                  "id": "wrist_mouse_tracking",
                  "text": ""
                }
              }
            ]
        }
    ]
}
```