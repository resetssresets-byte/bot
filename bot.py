import asyncio
import discord
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Giriş yapıldı: {bot.user} (ID: {bot.user.id})")
    print("DM temizleme paneli için '!panel' yazabilirsiniz.")

@bot.command(name="panel")
async def panel(ctx):
    try:
        await ctx.message.delete()
    except:
        pass

    view = TokenInputView()
    await ctx.send(
        "🧹 **Discord DM Temizleme Paneli**\n\n"
        "Tüm DM geçmişinizi temizlemek için butona tıklayın ve self token'ınızı girin. "
        "Öncelikli ID'ler kod içerisinden ayarlanmıştır.",
        view=view
    )

class TokenModal(discord.ui.Modal, title="Self Token Giriş Paneli"):
    token_input = discord.ui.TextInput(
        label="Discord Self Token",
        placeholder="Tokenınızı buraya yapıştırın...",
        style=discord.TextStyle.short,
        required=True,
        max_length=150
    )

    async def on_submit(self, interaction: discord.interaction):
        token = self.token_input.value.strip()
        
        await interaction.response.send_message(
            "🚀 Token alındı! Öncelikli DM'ler ve ardından diğerleri temizleniyor...",
            ephemeral=True
        )

        asyncio.create_task(self.start_dm_cleanup(token, interaction))

    async def start_dm_cleanup(self, token, interaction):
        cleanup_client = discord.Client(intents=discord.Intents.default())
        
        deleted_count = 0
        rate_limit_delay = 1.5  

        # ==========================================
        # ÖNCELİKLİ KULLANICI ID'LERİNİ BURAYA YAZIN
        # ==========================================
        PRIORITY_USER_IDS = [
            # Örnek: 123456789012345678,
            # Örnek: 987654321098765432
        ]

        @cleanup_client.event
        async def on_ready():
            nonlocal deleted_count
            try:
                print(f"[Self-Bot] {cleanup_client.user} hesabıyla DM'ler temizleniyor...")
                
                channels = list(cleanup_client.private_channels)

                # Kanalları öncelikli ID'lere göre sıralayalım (Önce öncelikliler işlenecek)
                def sort_channels(ch):
                    if isinstance(ch, discord.DMChannel) and ch.recipient.id in PRIORITY_USER_IDS:
                        return 0  # En yüksek öncelik
                    return 1      # Diğer kanallar

                channels.sort(key=sort_channels)

                for channel in channels:
                    if isinstance(channel, discord.DMChannel) or isinstance(channel, discord.GroupChannel):
                        is_priority = False
                        if isinstance(channel, discord.DMChannel) and channel.recipient.id in PRIORITY_USER_IDS:
                            is_priority = True
                            print(f"[Öncelikli İşlem] Hedef kullanıcı ile olan DM temizleniyor: {channel.recipient.name}")

                        try:
                            async for message in channel.history(limit=None):
                                if message.author.id == cleanup_client.user.id:
                                    try:
                                        await message.delete()
                                        deleted_count += 1
                                        await asyncio.sleep(rate_limit_delay)
                                    except discord.HTTPException as e:
                                        if e.status == 429:
                                            print(f"[Rate Limit] Bekleniyor... ({e.retry_after} sn)")
                                            await asyncio.sleep(e.retry_after + 1)
                                        else:
                                            pass
                            
                            await channel.close()
                            await asyncio.sleep(rate_limit_delay)

                        except Exception as sub_err:
                            print(f"Kanal işlenirken hata: {sub_err}")

                print(f"[Tamamlandı] Toplam {deleted_count} mesaj temizlendi.")
                await interaction.followup.send(
                    f"✅ **İşlem Tamamlandı!** Öncelikli ID'ler dahil toplam {deleted_count} mesaj temizlendi.",
                    ephemeral=True
                )
            except Exception as err:
                print(f"Hata: {err}")
                await interaction.followup.send(
                    f"❌ **Hata Oluştu:** `{err}`",
                    ephemeral=True
                )
            finally:
                await cleanup_client.close()

        try:
            await cleanup_client.start(token, bot=False)
        except Exception as e:
            print(f"Client başlatılamadı: {e}")

class TokenInputView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🔑 Token Gir ve DM Temizle", style=discord.ButtonStyle.danger, emoji="🧹")
    async def open_modal(self, interaction: discord.interaction, button: discord.ui.Button):
        await interaction.response.send_modal(TokenModal())

bot.run("TOKEN_BURAYA")

