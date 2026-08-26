import logging
import smtplib
from email.message import EmailMessage
from html import escape
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from config import Config

logger = logging.getLogger(__name__)


class EmailService:
	@staticmethod
	def send_organization_invitation(to_email: str, inviter_name: str, organization_name: str, role: str, invitation_url: str) -> dict:
		if not Config.SMTP_EMAIL or not Config.SMTP_PASSWORD:
			return {"success": False, "message": "Configuration SMTP incomplète."}
		safe_inviter = escape(inviter_name)
		safe_organization = escape(organization_name)
		safe_url = escape(invitation_url, quote=True)
		role_label = {
			"organizer": "Organisateur",
			"member": "Membre",
			"auditor": "Auditeur",
		}.get(role, role.capitalize())
		safe_role = escape(role_label)
		email = EmailMessage()
		email["From"] = f"MeetFlow <{Config.SMTP_EMAIL}>"
		email["To"] = to_email
		email["Subject"] = f"Invitation à rejoindre {organization_name} sur MeetFlow"
		email.set_content(
			"Bonjour,\n\n"
			f"{inviter_name} vous invite à rejoindre l'espace entreprise {organization_name} sur MeetFlow.\n"
			f"Rôle attribué : {role_label}.\n\n"
			"Pour accepter l'invitation, ouvrez le lien suivant :\n"
			f"{invitation_url}\n\n"
			f"Utilisez obligatoirement l'adresse {to_email} pour créer votre compte ou vous connecter.\n"
			"Vous accéderez ensuite directement à l'espace de votre entreprise.\n\n"
			"Si vous n'attendiez pas cette invitation, vous pouvez ignorer ce message."
		)
		email.add_alternative(
			f"""
			<div style="margin:0;background:#f5f7fb;padding:36px 16px;font-family:Arial,sans-serif;color:#181a1f">
			  <div style="max-width:600px;margin:0 auto;overflow:hidden;border:1px solid #e3e7f0;border-radius:20px;background:#ffffff;box-shadow:0 18px 50px rgba(16,24,40,.08)">
			    <div style="background:#17208a;padding:28px 34px;color:#ffffff">
			      <div style="font-size:20px;font-weight:800">MeetFlow</div>
			      <div style="margin-top:6px;font-size:13px;color:rgba(255,255,255,.68)">Intelligence de réunion pour les entreprises</div>
			    </div>
			    <div style="padding:34px">
			      <p style="margin:0 0 10px;font-size:13px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:#263bd8">Invitation entreprise</p>
			      <h1 style="margin:0;font-size:27px;line-height:1.25">Rejoignez {safe_organization}</h1>
			      <p style="margin:18px 0 0;font-size:15px;line-height:1.7;color:#5d6375"><strong style="color:#181a1f">{safe_inviter}</strong> vous invite à collaborer dans l'espace MeetFlow de <strong style="color:#181a1f">{safe_organization}</strong>.</p>
			      <div style="margin:24px 0;padding:16px 18px;border-radius:12px;background:#f5f7fb">
			        <div style="font-size:12px;color:#71788a">Rôle attribué</div>
			        <div style="margin-top:5px;font-size:16px;font-weight:700">{safe_role}</div>
			      </div>
			      <a href="{safe_url}" style="display:block;padding:15px 22px;border-radius:12px;background:#263bd8;color:#ffffff;text-align:center;text-decoration:none;font-size:15px;font-weight:700">Accepter l'invitation</a>
			      <p style="margin:22px 0 0;font-size:13px;line-height:1.65;color:#71788a">Créez votre compte ou connectez-vous avec l'adresse <strong>{escape(to_email)}</strong>. Une autre adresse ne pourra pas rejoindre cet espace.</p>
			      <p style="margin:22px 0 6px;font-size:12px;color:#8a90a0">Si le bouton ne fonctionne pas, copiez ce lien :</p>
			      <p style="margin:0;word-break:break-all;font-size:12px;line-height:1.6"><a href="{safe_url}" style="color:#263bd8">{safe_url}</a></p>
			    </div>
			  </div>
			  <p style="margin:18px auto 0;max-width:600px;text-align:center;font-size:11px;line-height:1.6;color:#8a90a0">Vous recevez cet e-mail parce qu'un administrateur MeetFlow a invité cette adresse. Si vous n'êtes pas concerné, ignorez simplement ce message.</p>
			</div>
			""",
			subtype="html",
		)
		try:
			with smtplib.SMTP(Config.SMTP_SERVER, Config.SMTP_PORT, timeout=30) as smtp:
				smtp.ehlo(); smtp.starttls(); smtp.ehlo()
				smtp.login(Config.SMTP_EMAIL, Config.SMTP_PASSWORD)
				smtp.send_message(email)
			return {"success": True}
		except (smtplib.SMTPException, OSError):
			logger.exception("Échec de l'envoi de l'invitation entreprise")
			return {"success": False, "message": "L'invitation n'a pas pu être envoyée."}

	@staticmethod
	def send_verification_code(to_email: str, recipient_name: str, code: str) -> dict:
		"""Envoie le code OTP de validation du compte MeetFlow."""
		if not Config.SMTP_EMAIL or not Config.SMTP_PASSWORD:
			message = "Configuration SMTP incomplète (SMTP_EMAIL / SMTP_PASSWORD)."
			logger.error(message)
			return {"success": False, "message": message}

		safe_name = escape(recipient_name)
		email = EmailMessage()
		email["From"] = f"MeetFlow <{Config.SMTP_EMAIL}>"
		email["To"] = to_email
		email["Subject"] = f"{code} — Votre code de vérification MeetFlow"
		email.set_content(
			f"Bonjour {recipient_name},\n\n"
			f"Votre code de vérification MeetFlow est : {code}\n\n"
			f"Il expire dans {Config.OTP_EXPIRY_MINUTES} minutes. "
			"Si vous n'êtes pas à l'origine de cette demande, ignorez cet email."
		)
		email.add_alternative(
			f"""
			<div style="font-family:Arial,sans-serif;background:#f6f7fb;padding:32px;color:#181a1f">
			  <div style="max-width:520px;margin:auto;background:#fff;border:1px solid #e6e8ef;border-radius:16px;padding:32px">
			    <div style="font-weight:700;font-size:20px;color:#263bd8">MeetFlow</div>
			    <h1 style="font-size:24px;margin:28px 0 12px">Confirmez votre adresse email</h1>
			    <p style="line-height:1.6;color:#5d6375">Bonjour {safe_name}, utilisez le code ci-dessous pour activer votre compte.</p>
			    <div style="margin:28px 0;padding:18px;text-align:center;background:#f2f4f8;border-radius:12px;font-size:32px;font-weight:700;letter-spacing:8px;color:#17208a">{code}</div>
			    <p style="font-size:14px;line-height:1.6;color:#71788a">Ce code expire dans {Config.OTP_EXPIRY_MINUTES} minutes. Ne le communiquez à personne.</p>
			  </div>
			</div>
			""",
			subtype="html",
		)

		try:
			with smtplib.SMTP(Config.SMTP_SERVER, Config.SMTP_PORT, timeout=30) as smtp:
				smtp.ehlo()
				smtp.starttls()
				smtp.ehlo()
				smtp.login(Config.SMTP_EMAIL, Config.SMTP_PASSWORD)
				smtp.send_message(email)
			logger.info("Code de vérification envoyé à %s", to_email)
			return {"success": True}
		except smtplib.SMTPAuthenticationError:
			logger.exception("Authentification SMTP refusée pour l'envoi du code OTP")
			return {"success": False, "message": "L'authentification au serveur email a échoué."}
		except (smtplib.SMTPException, OSError):
			logger.exception("Échec de l'envoi du code OTP")
			return {"success": False, "message": "Le code n'a pas pu être envoyé pour le moment."}

	@staticmethod
	def send_password_reset_code(to_email: str, recipient_name: str, code: str) -> dict:
		"""Envoie le code OTP permettant de choisir un nouveau mot de passe."""
		if not Config.SMTP_EMAIL or not Config.SMTP_PASSWORD:
			return {"success": False, "message": "Configuration SMTP incomplète."}
		safe_name = escape(recipient_name)
		email = EmailMessage()
		email["From"] = f"MeetFlow <{Config.SMTP_EMAIL}>"
		email["To"] = to_email
		email["Subject"] = f"{code} — Réinitialisation de votre mot de passe MeetFlow"
		email.set_content(
			f"Bonjour {recipient_name},\n\nVotre code de réinitialisation est : {code}\n\n"
			f"Il expire dans {Config.OTP_EXPIRY_MINUTES} minutes. "
			"Si vous n'êtes pas à l'origine de cette demande, ignorez cet email."
		)
		email.add_alternative(
			f"""
			<div style="font-family:Arial,sans-serif;background:#f6f7fb;padding:32px;color:#181a1f">
			  <div style="max-width:520px;margin:auto;background:#fff;border:1px solid #e6e8ef;border-radius:16px;padding:32px">
			    <div style="font-weight:700;font-size:20px;color:#263bd8">MeetFlow</div>
			    <h1 style="font-size:24px;margin:28px 0 12px">Réinitialisez votre mot de passe</h1>
			    <p style="line-height:1.6;color:#5d6375">Bonjour {safe_name}, utilisez ce code pour choisir un nouveau mot de passe.</p>
			    <div style="margin:28px 0;padding:18px;text-align:center;background:#f2f4f8;border-radius:12px;font-size:32px;font-weight:700;letter-spacing:8px;color:#17208a">{code}</div>
			    <p style="font-size:14px;line-height:1.6;color:#71788a">Ce code expire dans {Config.OTP_EXPIRY_MINUTES} minutes et ne peut être utilisé qu'une fois.</p>
			  </div>
			</div>
			""",
			subtype="html",
		)
		try:
			with smtplib.SMTP(Config.SMTP_SERVER, Config.SMTP_PORT, timeout=30) as smtp:
				smtp.ehlo(); smtp.starttls(); smtp.ehlo()
				smtp.login(Config.SMTP_EMAIL, Config.SMTP_PASSWORD)
				smtp.send_message(email)
			return {"success": True}
		except (smtplib.SMTPException, OSError):
			logger.exception("Échec de l'envoi du code de réinitialisation")
			return {"success": False, "message": "Le code n'a pas pu être envoyé."}

	@staticmethod
	def send_report(from_addr: str, to_emails: list[str], subject: str,
					html_body: str, pdf_path: str) -> dict:
		"""
		Envoie un rapport PDF via SMTP (Gmail).

		Args:
			from_addr: Adresse expéditeur (ex: "Assistant IA <user@gmail.com>")
			to_emails: Liste d'adresses destinataires
			subject:   Sujet du message
			html_body: Contenu HTML du message
			pdf_path:  Chemin vers le fichier PDF à attacher

		Retourne un dict: { success: bool, sent: int, failed: int, errors: [...] }
		"""
		if not Config.SMTP_EMAIL or not Config.SMTP_PASSWORD:
			msg = "Configuration SMTP incomplète (SMTP_EMAIL / SMTP_PASSWORD)"
			logger.error(msg)
			return {"success": False, "message": msg}

		try:
			with open(pdf_path, "rb") as f:
				pdf_bytes = f.read()
		except Exception as e:
			logger.exception("Impossible de lire le PDF pour envoi")
			return {"success": False, "message": "Impossible de lire le PDF.", "error": str(e)}

		if isinstance(to_emails, str):
			to_emails = [to_emails]
		if not isinstance(to_emails, list):
			return {"success": False, "message": "La liste des destinataires est invalide."}

		to_emails = [email.strip() for email in to_emails if email and str(email).strip()]
		if not to_emails:
			return {"success": False, "message": "Aucun destinataire valide fourni."}

		sender = Config.SMTP_EMAIL
		display_from = from_addr or f"Assistant IA <{sender}>"

		try:
			message = MIMEMultipart()
			message["From"] = display_from
			message["To"] = ", ".join(to_emails)
			message["Subject"] = subject
			message.attach(MIMEText(html_body, "html"))

			pdf_attachment = MIMEApplication(pdf_bytes, _subtype="pdf")
			pdf_attachment.add_header(
				"Content-Disposition",
				"attachment",
				filename="compte_rendu.pdf",
			)
			message.attach(pdf_attachment)

			with smtplib.SMTP(Config.SMTP_SERVER, Config.SMTP_PORT, timeout=30) as smtp:
				smtp.ehlo()
				smtp.starttls()
				smtp.ehlo()
				smtp.login(Config.SMTP_EMAIL, Config.SMTP_PASSWORD)
				smtp.sendmail(sender, to_emails, message.as_string())

			sent = len(to_emails)
			logger.info(
				"Email envoyé via SMTP à %s destinataire(s): %s",
				sent,
				", ".join(to_emails),
			)
			return {"success": True, "sent": sent, "failed": 0, "response": {"sent": sent}}

		except smtplib.SMTPAuthenticationError as e:
			logger.exception("Authentification SMTP refusée pour %s", Config.SMTP_EMAIL)
			errors = [{"email": email, "error": str(e)} for email in to_emails]
			return {
				"success": False,
				"sent": 0,
				"failed": len(to_emails),
				"errors": errors,
				"message": (
					f"Authentification Gmail refusée pour {Config.SMTP_EMAIL}. "
					"Utilisez un mot de passe d'application Gmail (16 caractères), "
					"pas le mot de passe du compte. "
					"Créez-en un sur https://myaccount.google.com/apppasswords "
					"puis mettez-le dans SMTP_PASSWORD du fichier .env."
				),
			}
		except smtplib.SMTPException as e:
			logger.exception("Erreur SMTP lors de l'envoi")
			errors = [{"email": email, "error": str(e)} for email in to_emails]
			return {
				"success": False,
				"sent": 0,
				"failed": len(to_emails),
				"errors": errors,
				"message": (
					"Aucun email n'a pu être envoyé. "
					"Vérifiez vos identifiants SMTP et que l'accès aux applications "
					"est activé sur votre compte Gmail."
				),
			}
		except Exception as e:
			logger.exception("Erreur lors de l'envoi via SMTP")
			errors = [{"email": email, "error": str(e)} for email in to_emails]
			return {
				"success": False,
				"sent": 0,
				"failed": len(to_emails),
				"errors": errors,
				"message": "Aucun email n'a pu être envoyé.",
			}
