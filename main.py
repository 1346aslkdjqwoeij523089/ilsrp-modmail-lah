import os
import logging
from flask import Flask
from threading import Thread
import asyncio
from datetime import datetime

import nextcord
from nextcord.ext import commands
from nextcord import Interaction, Embed, SelectOption, ButtonStyle
from nextcord.ui import View, Select, Button

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('nextcord')
logger.setLevel(logging.INFO)

# Flask app for UptimeRobot
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot 1 is running!"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run_flask)
    t.daemon = True
    t.start()

# Bot setup
intents = nextcord.Intents.default()
intents.message_content = True
bot = commands.Bot(intents=intents, help_command=None)

# Constants
ASSISTANCE_CHANNEL_ID = 1471666959753154646
TRANSCRIPT_CHANNEL_ID = 1471690459251478662

# Category IDs
CATEGORY_IDS = {
    "General Inquiry": 1471689868022120468,
    "Punishment Appeal": 1471689978135183581,
    "Staff Team Report": 1473172223501144306,
    "Employment Enquiry": 1473449632842518569,
    "Server Partnership": 1473449548692062391,
    "Management Request": 1471690051078455386
}

# Role IDs
ROLES = {
    "Evaluation": 1472072792081170682,
    "Supervision": 1471641790112333867,
    "Management": 1471641915215843559,
    "Executive": 1471642126663024640,
    "Holding": 1471642360503992411
}

# Permission configurations for each ticket type
TICKET_PERMISSIONS = {
    "General Inquiry": {
        "roles": ["Evaluation", "Supervision", "Management", "Executive", "Holding"],
        "perms": {
            "view_channel": True,
            "send_messages": True,
            "embed_links": True,
            "attach_files": True,
            "add_reactions": True,
            "read_message_history": True,
            "use_application_commands": True
        }
    },
    "Punishment Appeal": {
        "roles": ["Evaluation", "Supervision", "Management", "Executive", "Holding"],
        "perms": {
            "view_channel": True,
            "send_messages": True,
            "embed_links": True,
            "attach_files": True,
            "add_reactions": True,
            "read_message_history": True,
            "use_application_commands": True
        }
    },
    "Staff Team Report": {
        "roles": ["Supervision", "Management", "Executive", "Holding"],
        "perms": {
            "view_channel": True,
            "send_messages": True,
            "embed_links": True,
            "attach_files": True,
            "add_reactions": True,
            "read_message_history": True,
            "use_application_commands": True
        }
    },
    "Employment Enquiry": {
        "roles": ["Management", "Executive", "Holding"],
        "perms": {
            "view_channel": True,
            "send_messages": True,
            "embed_links": True,
            "attach_files": True,
            "add_reactions": True,
            "read_message_history": True,
            "use_application_commands": True
        }
    },
    "Server Partnership": {
        "roles": ["Executive", "Holding"],
        "perms": {
            "view_channel": True,
            "send_messages": True,
            "embed_links": True,
            "attach_files": True,
            "add_reactions": True,
            "read_message_history": True,
            "use_application_commands": True
        }
    },
    "Management Request": {
        "roles": ["Management", "Executive", "Holding"],
        "perms": {
            "view_channel": True,
            "send_messages": True,
            "embed_links": True,
            "attach_files": True,
            "add_reactions": True,
            "read_message_history": True,
            "use_application_commands": True
        }
    }
}

# Naming system
TICKET_NAMES = {
    "General Inquiry": "gi",
    "Punishment Appeal": "pa",
    "Staff Team Report": "str",
    "Employment Enquiry": "ee",
    "Server Partnership": "sp",
    "Management Request": "mgr"
}

# Sidebar colors
COLORS = {
    "General Inquiry": 0x30a2e0,
    "Punishment Appeal": 0xff6b6b,
    "Staff Team Report": 0xffd93d,
    "Employment Enquiry": 0x6bcb77,
    "Server Partnership": 0x9b59b6,
    "Management Request": 0xe74c3c
}


class TicketSelect(View):
    def __init__(self):
        super().__init__()
        select = Select(
            placeholder="Select an Assistance Category",
            options=[
                SelectOption(
                    label="General Inquiry",
                    value="General Inquiry",
                    emoji=nextcord.PartialEmoji(name="GeneralInquiry", id=1471679744767426581)
                ),
                SelectOption(
                    label="Punishment Appeal",
                    value="Punishment Appeal",
                    emoji=nextcord.PartialEmoji(name="PunishmentAppeal", id=1471679782818418852)
                ),
                SelectOption(
                    label="Staff Team Report",
                    value="Staff Team Report",
                    emoji=nextcord.PartialEmoji(name="StaffReport", id=1473438936285052968)
                ),
                SelectOption(
                    label="Employment Enquiry",
                    value="Employment Enquiry",
                    emoji=nextcord.PartialEmoji(name="EmploymentEnquiry", id=1473439147275325511)
                ),
                SelectOption(
                    label="Server Partnership",
                    value="Server Partnership",
                    emoji=nextcord.PartialEmoji(name="ServerPartnership", id=1473439109686104134)
                ),
                SelectOption(
                    label="Management Request",
                    value="Management Request",
                    emoji=nextcord.PartialEmoji(name="ManagementRequest", id=1471679839667879956)
                )
            ]
        )
        select.callback = self.select_callback
        self.add_item(select)

    async def select_callback(self, interaction: Interaction):
        # Get the selected value from the interaction data
        try:
            values = interaction.data.get("values", [])
            if not values:
                await interaction.response.send_message("Error: No category selected!", ephemeral=True)
                return
            ticket_type = values[0]
        except AttributeError:
            # Fallback: try to get from custom_id or other means
            await interaction.response.send_message("Error: Could not get selection!", ephemeral=True)
            return
        
        await create_ticket(interaction, ticket_type)


async def create_ticket(interaction: Interaction, ticket_type: str):
    user = interaction.user
    guild = interaction.guild
    
    # Get category
    category_id = CATEGORY_IDS[ticket_type]
    category = nextcord.utils.get(guild.categories, id=category_id)
    
    if not category:
        await interaction.response.send_message("Error: Ticket category not found!", ephemeral=True)
        return
    
    # Create channel name
    channel_name = f"{TICKET_NAMES[ticket_type]}-{user.name}".lower()
    
    # Get permission overwrites
    overwrites = {}
    
    # Get ticket opener's permission
    overwrites[user] = nextcord.PermissionOverwrite(
        view_channel=True,
        send_messages=True,
        embed_links=True,
        attach_files=True,
        add_reactions=True,
        read_message_history=True,
        use_application_commands=True
    )
    
    # Add role permissions
    perm_config = TICKET_PERMISSIONS[ticket_type]
    for role_name in perm_config["roles"]:
        role_id = ROLES[role_name]
        role = guild.get_role(role_id)
        if role:
            perms = perm_config["perms"]
            overwrites[role] = nextcord.PermissionOverwrite(
                view_channel=perms["view_channel"],
                send_messages=perms["send_messages"],
                embed_links=perms["embed_links"],
                attach_files=perms["attach_files"],
                add_reactions=perms["add_reactions"],
                read_message_history=perms["read_message_history"],
                use_application_commands=perms["use_application_commands"]
            )
    
    # Create the ticket channel
    ticket_channel = await category.create_text_channel(
        name=channel_name,
        overwrites=overwrites
    )
    
    # Send welcome embeds
    color = COLORS[ticket_type]
    
    # Get emojis for the ticket type
    emoji_map = {
        "General Inquiry": "<:GeneralInquiry:1471679744767426581>",
        "Punishment Appeal": "<:PunishmentAppeal:1471679782818418852>",
        "Staff Team Report": "<:StaffReport:1473438936285052968>",
        "Employment Enquiry": "<:EmploymentEnquiry:1473439147275325511>",
        "Server Partnership": "<:ServerPartnership:1473439109686104134>",
        "Management Request": "<:ManagementRequest:1471679839667879956>"
    }
    
    evaluation_role = guild.get_role(ROLES["Evaluation"])
    ping_text = f"{user.mention}"
    if evaluation_role:
        ping_text += f" {evaluation_role.mention}"
    
    # Create view with Close and Claim buttons
    view = TicketButtons(ticket_type=ticket_type, ticket_opener_id=user.id)
    
    if ticket_type == "General Inquiry":
        # Image Embed 1
        embed1 = Embed()
        embed1.set_image(url="https://media.discordapp.net/attachments/1472412365415776306/1478224780317425715/ilsrpgi.png?ex=69a79f9b&is=69a64e1b&hm=338881ebd5f579dba025d3b4f27e9aecd30a7ea8b6d5fbdf7722b333341dde99==&format=webp&quality=lossless&width=1357&height=678")
        embed1.color = color
        
        # Text Embed 2
        embed2 = Embed(
            title=f"You have created a General Inquiry {emoji_map[ticket_type]}",
            description=f"Thank you for creating a __General Inquiry__.\n> Please await an Evaluator <:EvaluationTeam:1477360862594596914> to handle your request. In the meanwhile, please state your request. Refrain from pinging any staff members, or your ticket will be instantly closed.",
            color=color
        )
        
        # Image Embed 3
        embed3 = Embed()
        embed3.set_image(url="https://cdn.discordapp.com/attachments/1472412365415776306/1477490966116962344/ilsrpfooter.png?ex=69a79730&is=69a645b0&hm=c4fc3a52fd42dc7ace7849e05eb3ed16f6c79abb4f3bd5dd27eef446b1d28ad5&")
        embed3.color = color
        
        await ticket_channel.send(content=ping_text)
        await ticket_channel.send(embeds=[embed1, embed2, embed3], view=view)
    else:
        # Generic welcome embed for other ticket types
        embed = Embed(
            title=f"You have created a {ticket_type} {emoji_map[ticket_type]}",
            description=f"Thank you for creating a __**{ticket_type}**__. Please wait for a staff member to assist you.",
            color=color
        )
        await ticket_channel.send(content=ping_text, embed=embed, view=view)
    
    await interaction.response.send_message(f"Ticket created: {ticket_channel.mention}", ephemeral=True)


class TicketButtons(View):
    def __init__(self, ticket_type: str, ticket_opener_id: int):
        super().__init__()
        self.ticket_type = ticket_type
        self.ticket_opener_id = ticket_opener_id
        
        # Close Button
        close_button = Button(
            style=ButtonStyle.red,
            label="Close",
            custom_id="close_ticket"
        )
        close_button.callback = self.close_callback
        self.add_item(close_button)
        
        # Claim Button
        claim_button = Button(
            style=ButtonStyle.blurple,
            label="Claim",
            custom_id="claim_ticket"
        )
        claim_button.callback = self.claim_callback
        self.add_item(claim_button)
    
    async def close_callback(self, interaction: Interaction):
        channel = interaction.channel
        
        # Check if user has permission to close (staff role)
        user = interaction.user
        guild = interaction.guild
        
        # Get allowed roles for this ticket type
        allowed_roles = TICKET_PERMISSIONS[self.ticket_type]["roles"]
        user_roles = [role.id for role in user.roles]
        
        has_permission = False
        for role_name in allowed_roles:
            if ROLES[role_name] in user_roles:
                has_permission = True
                break
        
        if not has_permission:
            await interaction.response.send_message("You don't have permission to close this ticket!", ephemeral=True)
            return
        
        # Collect messages for transcript
        transcript_messages = []
        async for message in channel.history(limit=None, oldest_first=True):
            timestamp = message.created_at.strftime("%Y-%m-%d %H:%M:%S")
            content = message.content if message.content else "[No text content]"
            transcript_messages.append(f"[{timestamp}] {message.author.name}#{message.author.discriminator}: {content}")
        
        transcript_text = "\n".join(transcript_messages)
        
        # Send transcript to transcript channel
        transcript_channel = guild.get_channel(TRANSCRIPT_CHANNEL_ID)
        if transcript_channel:
            transcript_embed = Embed(
                title=f"Ticket Closed: {self.ticket_type}",
                description=f"**Ticket Opener:** {interaction.user.name}#{interaction.user.discriminator}\n**Closed By:** {user.name}#{user.discriminator}\n\n**Transcript:**\n```\n{transcript_text[:4000]}\n```",
                color=0xff0000,
                timestamp=datetime.now()
            )
            await transcript_channel.send(embed=transcript_embed)
        
        # Delete the channel
        await channel.delete()
    
    async def claim_callback(self, interaction: Interaction):
        user = interaction.user
        
        # Check if the user is the ticket opener
        if user.id == self.ticket_opener_id:
            color = COLORS[self.ticket_type]
            
            # Send error message
            embed1 = Embed(
                description="Unfortunately, you are unable to claim your own ticket. Please wait for a staff member to assist you.",
                color=color
            )
            
            embed2 = Embed()
            embed2.set_image(url="https://cdn.discordapp.com/attachments/1472412365415776306/1477490966116962344/ilsrpfooter.png?ex=69a79730&is=69a645b0&hm=c4fc3a52fd42dc7ace7849e05eb3ed16f6c79abb4f3bd5dd27eef446b1d28ad5&")
            embed2.color = color
            
            await interaction.response.send_message(embeds=[embed1, embed2], ephemeral=True)
            return
        
        # Check if user has permission to claim (must be Evaluation+ for General Inquiry)
        if self.ticket_type == "General Inquiry":
            allowed_roles = TICKET_PERMISSIONS[self.ticket_type]["roles"]
            user_roles = [role.id for role in user.roles]
            
            has_permission = False
            for role_name in allowed_roles:
                if ROLES[role_name] in user_roles:
                    has_permission = True
                    break
            
            if not has_permission:
                await interaction.response.send_message("You don't have permission to claim this ticket!", ephemeral=True)
                return
        
        # Claim the ticket
        color = COLORS[self.ticket_type]
        embed = Embed(
            description=f"{user.mention} has claimed this ticket!",
            color=color
        )
        await interaction.response.send_message(embed=embed)


@bot.event
async def on_ready():
    """Bot is ready and logged in."""
    logger.info(f'Bot 1 logged in as {bot.user}')
    
    # Setup the assistance channel with dropdown
    guild = bot.guilds[0]
    assistance_channel = guild.get_channel(ASSISTANCE_CHANNEL_ID)
    
    if assistance_channel:
        # Create the embed
        embed = Embed(
            title="🎫 Welcome to Illinois State Roleplay Support",
            description="Please select a category from the dropdown below to create a ticket.",
            color=0x30a2e0
        )
        
        # Create view with dropdown
        view = TicketSelect()
        
        # Check if there's already a message with the dropdown
        async for message in assistance_channel.history(limit=10):
            if message.author == bot.user:
                await message.delete()
        
        await assistance_channel.send(embed=embed, view=view)
        logger.info("Ticket system setup complete!")


@bot.event
async def on_message(message):
    """Handle messages in ticket channels."""
    # This can be extended to handle auto-responses or logging
    pass


# Run the bot
if __name__ == "__main__":
    TOKEN = os.environ.get("TOKEN")
    if not TOKEN:
        logger.error("TOKEN environment variable not set!")
        print("ERROR: Please set the TOKEN environment variable!")
        exit(1)
    
    # Start Flask server for UptimeRobot
    keep_alive()
    
    # Run the bot
    bot.run(TOKEN)

