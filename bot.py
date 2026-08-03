import discord
from discord import app_commands
from discord.ext import commands
import aiohttp
import asyncio
import json
from datetime import datetime
import os
import sqlite3

# Настройки бота
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='/', intents=intents)

# Инициализация базы данных
def init_db():
    conn = sqlite3.connect('connections.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS connections
                 (discord_id TEXT PRIMARY KEY, roblox_username TEXT, roblox_id TEXT)''')
    conn.commit()
    conn.close()

init_db()

# Цвета для форматирования
COLORS = {
    'red': 0xFF0000,
    'green': 0x00FF00,
    'blue': 0x0000FF,
    'yellow': 0xFFFF00,
    'purple': 0x800080,
    'orange': 0xFFA500,
    'pink': 0xFF69B4,
    'cyan': 0x00FFFF,
    'white': 0xFFFFFF,
    'black': 0x000000
}

# ID группы Roblox (ЗАМЕНИ НА СВОЙ)
GROUP_ID = 35984818  # <-- СЮДА ВСТАВЬ ID СВОЕЙ ГРУППЫ

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f'✅ Бот {bot.user} запущен!')
    print(f'✅ Слэш-команды синхронизированы!')
    await bot.change_presence(activity=discord.Game(name="/help для помощи"))

# ============ КОМАНДА /say ============
@bot.tree.command(name="say", description="Отправить форматированное сообщение с цветом")
@app_commands.describe(
    color="Выберите цвет сообщения",
    message="Текст сообщения"
)
@app_commands.choices(color=[
    app_commands.Choice(name="🔴 Красный", value="red"),
    app_commands.Choice(name="🟢 Зеленый", value="green"),
    app_commands.Choice(name="🔵 Синий", value="blue"),
    app_commands.Choice(name="🟡 Желтый", value="yellow"),
    app_commands.Choice(name="🟣 Фиолетовый", value="purple"),
    app_commands.Choice(name="🟠 Оранжевый", value="orange"),
    app_commands.Choice(name="🩷 Розовый", value="pink"),
    app_commands.Choice(name="🩵 Голубой", value="cyan"),
    app_commands.Choice(name="⚪ Белый", value="white"),
    app_commands.Choice(name="⚫ Черный", value="black")
])
async def say(interaction: discord.Interaction, color: app_commands.Choice[str], message: str):
    embed_color = COLORS.get(color.value, 0x00FF00)
    
    embed = discord.Embed(
        description=message,
        color=embed_color,
        timestamp=datetime.now()
    )
    embed.set_footer(text=f"Отправлено: {interaction.user.name}")
    embed.set_author(name=interaction.user.display_name, icon_url=interaction.user.avatar.url if interaction.user.avatar else None)
    
    await interaction.response.send_message(embed=embed)

# ============ КОМАНДА /studioinfo ============
@bot.tree.command(name="studioinfo", description="Получить информацию о студии Roblox")
async def studioinfo(interaction: discord.Interaction):
    await interaction.response.defer()
    
    try:
        async with aiohttp.ClientSession() as session:
            # Получаем информацию о группе
            async with session.get(f'https://groups.roblox.com/v1/groups/{GROUP_ID}') as response:
                if response.status == 200:
                    group_data = await response.json()
                    
                    # Получаем количество участников
                    async with session.get(f'https://groups.roblox.com/v1/groups/{GROUP_ID}/users?limit=100') as users_response:
                        users_data = await users_response.json() if users_response.status == 200 else {'data': []}
                    
                    # Получаем количество игр
                    async with session.get(f'https://games.roblox.com/v2/groups/{GROUP_ID}/games?limit=10') as games_response:
                        games_data = await games_response.json() if games_response.status == 200 else {'data': []}
                    
                    # Создаем красивое embed сообщение
                    embed = discord.Embed(
                        title=f"🏢 {group_data.get('name', 'Неизвестно')}",
                        description="📊 **Информация о студии**",
                        color=0x00FF00,
                        timestamp=datetime.now()
                    )
                    
                    # Основная информация
                    created_date = datetime.fromisoformat(group_data.get('created', '2024-01-01T00:00:00Z')[:-1])
                    embed.add_field(
                        name="📅 Дата создания",
                        value=f"<t:{int(created_date.timestamp())}:D>",
                        inline=True
                    )
                    
                    embed.add_field(
                        name="👥 Участников",
                        value=f"**{len(users_data.get('data', []))}**",
                        inline=True
                    )
                    
                    embed.add_field(
                        name="🎮 Игр",
                        value=f"**{len(games_data.get('data', []))}**",
                        inline=True
                    )
                    
                    # Статус группы
                    owner = group_data.get('owner', {})
                    embed.add_field(
                        name="👑 Владелец",
                        value=owner.get('displayName', owner.get('name', 'Неизвестно')),
                        inline=True
                    )
                    
                    embed.add_field(
                        name="🔗 Ссылка",
                        value=f"[Перейти в группу](https://www.roblox.com/groups/{GROUP_ID})",
                        inline=True
                    )
                    
                    # Описание
                    if group_data.get('description'):
                        desc = group_data['description'][:500] + ('...' if len(group_data['description']) > 500 else '')
                        embed.add_field(
                            name="📝 Описание",
                            value=desc,
                            inline=False
                        )
                    
                    # Иконка
                    if group_data.get('emblemUrl'):
                        embed.set_thumbnail(url=group_data['emblemUrl'])
                    
                    embed.set_footer(text="Информация актуальна на момент запроса")
                    
                    await interaction.followup.send(embed=embed)
                else:
                    await interaction.followup.send("❌ Не удалось получить информацию о студии")
                    
    except Exception as e:
        await interaction.followup.send(f"❌ Произошла ошибка: {str(e)}")

# ============ КОМАНДА /profile ============
@bot.tree.command(name="profile", description="Показать профиль пользователя Discord")
@app_commands.describe(
    user="Пользователь, информацию о котором хотите увидеть"
)
async def profile(interaction: discord.Interaction, user: discord.Member = None):
    if not user:
        user = interaction.user
    
    embed = discord.Embed(
        title=f"👤 Профиль {user.name}",
        color=user.color if user.color != 0 else 0x00FF00,
        timestamp=datetime.now()
    )
    
    # Аватар
    embed.set_thumbnail(url=user.avatar.url if user.avatar else user.default_avatar.url)
    
    # Основная информация
    embed.add_field(name="📛 Имя", value=user.name, inline=True)
    embed.add_field(name="🔢 ID", value=f"`{user.id}`", inline=True)
    embed.add_field(name="📅 Аккаунт создан", value=f"<t:{int(user.created_at.timestamp())}:D>", inline=True)
    embed.add_field(name="📆 Присоединился", value=f"<t:{int(user.joined_at.timestamp())}:D>", inline=True)
    
    # Статус
    status_emoji = {
        discord.Status.online: "🟢",
        discord.Status.idle: "🟡",
        discord.Status.dnd: "🔴",
        discord.Status.offline: "⚫"
    }
    status = status_emoji.get(user.status, "⚫")
    embed.add_field(name="📊 Статус", value=f"{status} {str(user.status).capitalize()}", inline=True)
    
    # Роли
    roles = [role.mention for role in user.roles[1:]]  # Исключаем @everyone
    if roles:
        embed.add_field(
            name=f"🎭 Роли ({len(roles)})",
            value=" ".join(roles[:10]) + ("..." if len(roles) > 10 else ""),
            inline=False
        )
    
    # Проверка привязки Roblox из БД
    conn = sqlite3.connect('connections.db')
    c = conn.cursor()
    c.execute('SELECT roblox_username FROM connections WHERE discord_id = ?', (str(user.id),))
    result = c.fetchone()
    conn.close()
    
    if result:
        embed.add_field(
            name="🎮 Roblox",
            value=f"Привязан: **{result[0]}**",
            inline=False
        )
    
    embed.set_footer(text=f"Запросил: {interaction.user.name}")
    
    await interaction.response.send_message(embed=embed)

# ============ КОМАНДА /connect ============
@bot.tree.command(name="connect", description="Привязать аккаунт Roblox к Discord")
@app_commands.describe(
    roblox_username="Ваш никнейм в Roblox"
)
async def connect(interaction: discord.Interaction, roblox_username: str):
    await interaction.response.defer()
    
    try:
        # Проверяем существование пользователя в Roblox
        async with aiohttp.ClientSession() as session:
            async with session.get(f'https://api.roblox.com/users/get-by-username?username={roblox_username}') as response:
                if response.status == 200:
                    user_data = await response.json()
                    user_id = user_data.get('Id')
                    
                    if user_id:
                        # Сохраняем привязку в БД
                        conn = sqlite3.connect('connections.db')
                        c = conn.cursor()
                        c.execute('INSERT OR REPLACE INTO connections (discord_id, roblox_username, roblox_id) VALUES (?, ?, ?)',
                                 (str(interaction.user.id), roblox_username, str(user_id)))
                        conn.commit()
                        conn.close()
                        
                        # Выдаем роль "Верифицированный"
                        role_name = "Верифицированный"
                        role = discord.utils.get(interaction.guild.roles, name=role_name)
                        
                        if not role:
                            # Создаем роль если её нет
                            role = await interaction.guild.create_role(
                                name=role_name,
                                color=discord.Color.green(),
                                reason="Создана для верификации пользователей"
                            )
                        
                        await interaction.user.add_roles(role)
                        
                        # Получаем информацию о пользователе для красивого отображения
                        async with session.get(f'https://users.roblox.com/v1/users/{user_id}') as user_info_response:
                            user_info = await user_info_response.json() if user_info_response.status == 200 else {}
                        
                        embed = discord.Embed(
                            title="✅ Успешная привязка!",
                            description=f"Аккаунт **{roblox_username}** успешно привязан к Discord!",
                            color=0x00FF00,
                            timestamp=datetime.now()
                        )
                        embed.add_field(name="🎮 Roblox ID", value=f"`{user_id}`", inline=True)
                        embed.add_field(name="📅 Дата регистрации в Roblox", 
                                      value=f"<t:{int(datetime.fromisoformat(user_info.get('created', '2024-01-01T00:00:00Z')[:-1]).timestamp())}:D>" if user_info.get('created') else "Неизвестно",
                                      inline=True)
                        embed.add_field(name="✅ Роль", value=f"Выдана роль {role.mention}", inline=False)
                        embed.set_thumbnail(url=f"https://www.roblox.com/headshot-thumbnail/image?userId={user_id}&width=420&height=420&format=png")
                        
                        await interaction.followup.send(embed=embed)
                    else:
                        await interaction.followup.send("❌ Пользователь с таким именем не найден в Roblox")
                else:
                    await interaction.followup.send("❌ Ошибка при проверке пользователя в Roblox")
                    
    except Exception as e:
        await interaction.followup.send(f"❌ Произошла ошибка: {str(e)}")

# ============ КОМАНДА /unconnect ============
@bot.tree.command(name="unconnect", description="Отвязать аккаунт Roblox от Discord")
async def unconnect(interaction: discord.Interaction):
    conn = sqlite3.connect('connections.db')
    c = conn.cursor()
    c.execute('SELECT roblox_username FROM connections WHERE discord_id = ?', (str(interaction.user.id),))
    result = c.fetchone()
    
    if result:
        c.execute('DELETE FROM connections WHERE discord_id = ?', (str(interaction.user.id),))
        conn.commit()
        conn.close()
        
        # Убираем роль
        role = discord.utils.get(interaction.guild.roles, name="Верифицированный")
        if role:
            await interaction.user.remove_roles(role)
        
        embed = discord.Embed(
            title="✅ Привязка удалена",
            description=f"Аккаунт **{result[0]}** успешно отвязан от Discord",
            color=0xFFA500,
            timestamp=datetime.now()
        )
        await interaction.response.send_message(embed=embed)
    else:
        conn.close()
        embed = discord.Embed(
            title="❌ Ошибка",
            description="У вас нет привязанного аккаунта Roblox",
            color=0xFF0000
        )
        await interaction.response.send_message(embed=embed)

# ============ КОМАНДА /help ============
@bot.tree.command(name="help", description="Показать список всех команд")
async def help_command(interaction: discord.Interaction):
    embed = discord.Embed(
        title="📚 Список команд",
        description="Все команды бота",
        color=0x00FF00,
        timestamp=datetime.now()
    )
    
    embed.add_field(
        name="/say [цвет] [сообщение]",
        value="Отправить форматированное сообщение с выбором цвета",
        inline=False
    )
    embed.add_field(
        name="/studioinfo",
        value="Получить информацию о студии Roblox",
        inline=False
    )
    embed.add_field(
        name="/profile [@user]",
        value="Показать профиль пользователя Discord",
        inline=False
    )
    embed.add_field(
        name="/connect [RobloxUsername]",
        value="Привязать аккаунт Roblox и получить роль",
        inline=False
    )
    embed.add_field(
        name="/unconnect",
        value="Отвязать аккаунт Roblox",
        inline=False
    )
    embed.add_field(
        name="/clear [количество]",
        value="Очистить сообщения в канале (только для администраторов)",
        inline=False
    )
    
    embed.set_footer(text=f"Запросил: {interaction.user.name}")
    embed.set_thumbnail(url=bot.user.avatar.url if bot.user.avatar else None)
    
    await interaction.response.send_message(embed=embed)

# ============ КОМАНДА /clear ============
@bot.tree.command(name="clear", description="Очистить сообщения в канале")
@app_commands.describe(
    amount="Количество сообщений для удаления (макс. 100)"
)
@commands.has_permissions(manage_messages=True)
async def clear(interaction: discord.Interaction, amount: int = 5):
    if amount > 100:
        await interaction.response.send_message("❌ Нельзя удалить больше 100 сообщений за раз", ephemeral=True)
        return
    
    await interaction.response.defer(ephemeral=True)
    
    deleted = await interaction.channel.purge(limit=amount)
    
    embed = discord.Embed(
        title="🧹 Очистка сообщений",
        description=f"Удалено {len(deleted)} сообщений",
        color=0x00FF00,
        timestamp=datetime.now()
    )
    
    await interaction.followup.send(embed=embed, ephemeral=True)

# ============ КОМАНДА /stats ============
@bot.tree.command(name="stats", description="Показать статистику бота")
async def stats(interaction: discord.Interaction):
    embed = discord.Embed(
        title="📊 Статистика бота",
        color=0x00FF00,
        timestamp=datetime.now()
    )
    
    embed.add_field(name="📌 Серверов", value=len(bot.guilds), inline=True)
    embed.add_field(name="👥 Всего пользователей", value=sum(guild.member_count for guild in bot.guilds), inline=True)
    embed.add_field(name="⏱️ Пинг", value=f"{round(bot.latency * 1000)}ms", inline=True)
    
    # Количество привязанных аккаунтов
    conn = sqlite3.connect('connections.db')
    c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM connections')
    count = c.fetchone()[0]
    conn.close()
    
    embed.add_field(name="🎮 Привязанных аккаунтов Roblox", value=count, inline=True)
    embed.add_field(name="🤖 Версия бота", value="2.0.0", inline=True)
    embed.add_field(name="📅 Запущен", value=f"<t:{int(datetime.now().timestamp())}:R>", inline=True)
    
    embed.set_footer(text=f"Запросил: {interaction.user.name}")
    embed.set_thumbnail(url=bot.user.avatar.url if bot.user.avatar else None)
    
    await interaction.response.send_message(embed=embed)

# ============ ОБРАБОТКА ОШИБОК ============
@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.errors.MissingPermissions):
        embed = discord.Embed(
            title="❌ Ошибка",
            description="У вас нет прав для использования этой команды!",
            color=0xFF0000
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
    else:
        embed = discord.Embed(
            title="❌ Ошибка",
            description=f"Произошла ошибка: {str(error)}",
            color=0xFF0000
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

# ============ ЗАПУСК БОТА ============
if __name__ == "__main__":
    token = os.environ.get('DISCORD_TOKEN')
    if not token:
        print("❌ Токен не найден! Установите переменную окружения DISCORD_TOKEN")
    else:
        bot.run(token)
