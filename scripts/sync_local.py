#!/usr/bin/env python3
"""
Roda localmente no seu Mac para coletar posts via Instaloader
e salvar direto no banco do Railway.

Uso:
  1. Coloque o DATABASE_URL do Railway no .env
  2. python scripts/sync_local.py
"""
import sys
import os
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv
load_dotenv()

from src.database import get_session
from src.models import Profile
from src.collector.instaloader_client import fetch_posts_instaloader
from src.models import Post


def sync_all():
    session = get_session()
    try:
        profiles = session.query(Profile).filter_by(active=True).all()
        if not profiles:
            print("Nenhum perfil cadastrado. Adicione perfis no dashboard primeiro.")
            return

        print(f"{len(profiles)} perfis encontrados.\n")

        for profile in profiles:
            print(f"Coletando @{profile.handle}...")
            try:
                raw_posts = fetch_posts_instaloader(profile.handle, months_back=1)
            except Exception as e:
                print(f"  ERRO ao coletar @{profile.handle}: {e}")
                continue

            existing_ids = {
                row[0] for row in session.query(Post.instagram_id)
                .filter_by(profile_id=profile.id).all()
            }

            novos = []
            for raw in raw_posts:
                if raw["instagram_id"] in existing_ids:
                    continue
                novos.append(Post(
                    profile_id=profile.id,
                    instagram_id=raw["instagram_id"],
                    image_url=raw["image_url"],
                    caption=raw["caption"],
                    hashtags=raw["hashtags"],
                    likes=raw["likes"],
                    comments=raw["comments"],
                    post_type=raw["post_type"],
                    published_at=raw["published_at"],
                ))

            session.add_all(novos)
            session.commit()
            print(f"  {len(novos)} novos posts salvos.\n")
            time.sleep(10)

        print("Sincronização concluída! Agora abra o dashboard e clique em 'Analisar posts'.")
    finally:
        session.close()


if __name__ == "__main__":
    sync_all()
