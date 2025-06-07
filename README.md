# wrist_mouse

Scripts for using the [doublepoint touch_sdk](https://github.com/doublepointlab/touch-sdk-py) and [WowMouse](https://play.google.com/store/apps/details?id=io.port6.watchbridge&pcampaignid=web_share)
in tandem with a keyboard layer as a mouse substitute.


* The main tracking script is standalone in `wrist_mouse_tracker.py`, which polls state from `~/.config/wrist_mouse/tracking_state` for decoupling
* `wrist_mouse_config.py toggle|set OFF|HAND_UP` will write the mode to 
* The talon integration piece is in wrist_mouse_toggler.py

```json
{
    "description": "Toggle wrist_mouse state",
    "manipulators": [
        {
            "type": "basic",
            "from": {
                "key_code": "f22"
            },
            "to": [{ "shell_command": "/bin/python /Users/mjr/.talon/user/wrist_mouse/wrist_mouse_config.py toggle" }]
        }
    ]
}
```