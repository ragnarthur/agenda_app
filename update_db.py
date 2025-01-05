from app import app  # Importe seu app Flask principal
from models import db, Contabilidade

with app.app_context():
    # 1) Ajustar data p/ "Aniversário Elder"
    elder = Contabilidade.query.filter_by(evento_titulo="Aniversário Elder").first()
    if elder:
        elder.data_evento_original = "2024-12-07"
        print("[OK] Aniversário Elder => data_evento_original=2024-12-07")
    else:
        print("[!] Não encontrado: 'Aniversário Elder'")

    # 2) Ajustar data p/ "Natal Waldemar JR."
    waldemar = Contabilidade.query.filter_by(evento_titulo="Natal Waldemar JR.").first()
    if waldemar:
        waldemar.data_evento_original = "2024-12-24"
        print("[OK] Natal Waldemar JR. => data_evento_original=2024-12-24")
    else:
        print("[!] Não encontrado: 'Natal Waldemar JR.'")

    # 3) Excluir "Evento Removido" c/ valor_bruto=1000.0
    removido_1000 = Contabilidade.query.filter_by(
        evento_titulo="Evento Removido", valor_bruto=1000.0
    ).first()
    if removido_1000:
        db.session.delete(removido_1000)
        print("[OK] Excluído: 'Evento Removido' valor_bruto=1000.0")
    else:
        print("[!] Não encontrado: 'Evento Removido' valor_bruto=1000.0")

    # 4) Excluir "Evento Removido" c/ valor_bruto=300.0
    removido_300 = Contabilidade.query.filter_by(
        evento_titulo="Evento Removido", valor_bruto=300.0
    ).first()
    if removido_300:
        db.session.delete(removido_300)
        print("[OK] Excluído: 'Evento Removido' valor_bruto=300.0")
    else:
        print("[!] Não encontrado: 'Evento Removido' valor_bruto=300.0")

    # Salvar as alterações
    db.session.commit()
    print("Alterações confirmadas.")
