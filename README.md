# Operationbot for the Zeus Operations discord

**Note:** Requires Python 3.9 or newer.

## Setting up

1. Create a new Discord bot at <https://discord.com/developers/applications>

   See [here](https://discordpy.readthedocs.io/en/latest/discord.html) for more
   detailed instructions. Note that the bot does not have to be marked as
   public.

2. Copy `secret.py.example` to `secret.py` and add your bot token. Other values
   can be customised as well but they are not critical for a basic setup.

3. Change the channel IDs in `config.py` if the bot is not running on the Zeus
   Operations discord.

4. Create a virtual environment:

   ```shell
   sudo apt install python3-venv python3-pip
   python3 -m venv venv
   ```

5. Activate the virtual environment:

   ```shell
   source venv/bin/activate
   ```

6. Install required packages:

   ```shell
   pip install -r requirements.txt
   ```
