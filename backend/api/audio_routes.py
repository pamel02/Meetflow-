"""HTTP routes for audio-segment ingestion and playback."""

from flask import Blueprint, jsonify, request, send_file

from middleware.jwt import jwt_required
from services.audio_service import AudioService

audio_bp = Blueprint("audio", __name__)


def _get_upload_data() -> dict:
    """Read text fields from a multipart request."""
    data = request.form.to_dict()
    return data or request.values.to_dict()


@audio_bp.route("/upload-segment", methods=["POST"])
@jwt_required
def upload_segment(current_user):
    """Store one audio segment and enqueue its transcription."""
    if "audio" not in request.files:
        return jsonify({"error": "Fichier audio manquant (champ 'audio')."}), 400

    uploaded_file = request.files["audio"]
    if not uploaded_file.filename:
        return jsonify({"error": "Nom de fichier vide."}), 400

    response, status = AudioService.upload_segment(
        user=current_user,
        data=_get_upload_data(),
        file=uploaded_file,
    )
    return jsonify(response), status


@audio_bp.route("/end-meeting", methods=["POST"])
@jwt_required
def end_meeting(current_user):
    """Close recording after all client uploads have completed."""
    data = request.get_json(silent=True) or {}
    response, status = AudioService.end_meeting(current_user, data)
    return jsonify(response), status


@audio_bp.route("/status/<int:meeting_id>", methods=["GET"])
@jwt_required
def get_audio_status(current_user, meeting_id: int):
    """Return detailed ingestion and transcription status."""
    response, status = AudioService.get_audio_status(current_user, meeting_id)
    return jsonify(response), status


@audio_bp.route("/file/<int:meeting_id>/<filename>", methods=["GET"])
@jwt_required
def get_audio_file(current_user, meeting_id: int, filename: str):
    """Serve an audio segment only to the meeting owner."""
    result, status = AudioService.get_audio_file(current_user, meeting_id, filename)
    if status != 200:
        return jsonify(result), status
    return send_file(result["path"], mimetype=result["mimetype"], conditional=True)
