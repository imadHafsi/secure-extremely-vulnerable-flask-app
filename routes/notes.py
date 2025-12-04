from json import dumps
from flask_login import login_required, current_user
from flask import request, redirect, flash
from app import app
from forms.note_form import NoteForm
from models import Session, Note
from utils.notes import get_notes_for_user
from utils.sanitizer import sanitize_note_text


@app.route('/notes', methods=['GET'])
@login_required
def get_notes():
    return get_notes_for_user(current_user.id)


@app.route('/notes', methods=['POST'])
@login_required
def add_note():
    form = NoteForm(request.form)

    if not form.validate():
        flash(dumps(form.errors), 'error')
    else:
        with Session(expire_on_commit=False) as session:
            raw_title = form.title.data
            clean_title = sanitize_note_text(raw_title)
            raw_text = form.text.data
            clean_text = sanitize_note_text(raw_text)
            note = Note(id=None,
                        created_at=None,
                        title=clean_title,
                        text=clean_text,
                        private=form.private.data,
                        user_id=current_user.id)
            session.add(note)
            session.commit()

        flash('Note created', 'success')

    return redirect('/home')


@app.route('/notes/<int:note_id>/delete', methods=['POST'])
@login_required
def delete_note(note_id: int):

    with Session() as session:
        note = session.get(Note, note_id)
        # One generic message: either note doesn't exist
        # or you're not allowed to reduce ID enumeration
        if note is None or not (current_user.is_admin or note.user_id == current_user.id):
            flash("You either don't have a note with that ID "
            "or you're not authorised to delete it", "warning")
        else:
            session.delete(note)
            session.commit()
            flash('Note deleted', 'info')

    return redirect('/home')

@app.route('/notes/<int:note_id>/edit', methods=['POST'])
@login_required
def edit_note(note_id):
    form = NoteForm(request.form)

    if not form.validate():
        flash(dumps(form.errors), 'error')
        return redirect('/home')

    with Session(expire_on_commit=False) as session:
        note = session.get(Note, note_id)
        
        if note is None or note.user_id != current_user.id:
            flash("You don't have a note with that ID", "warning")
        else:
            raw_title = form.title.data
            raw_text = form.text.data
            note.title = sanitize_note_text(raw_title)
            note.text = sanitize_note_text(raw_text)
            note.private = form.private.data
            session.commit()
            flash('Note updated', 'success')

    return redirect('/home')
