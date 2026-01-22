from typing import Iterable

import ollama

from app.config import Settings
from app import models


class LLMService:
    def __init__(self, settings: Settings):
        self.settings = settings
        # Create client with optional API token for cloud models
        client_kwargs = {"host": settings.ollama_api_base}
        if settings.ollama_api_token:
            client_kwargs["headers"] = {"Authorization": f"Bearer {settings.ollama_api_token}"}
        self.client = ollama.Client(**client_kwargs)

    def chat(
        self, history: Iterable[models.Message], user_message: str, ingredients: list[models.Ingredient] | None = None,
        user_settings: models.UserSettings | None = None
    ) -> str:
        # Build messages list for chat API
        messages = []
        
        # Add system prompt if configured
        system_content = self.settings.system_prompt or ""
        
        # Add ingredient data to system context if available
        add_content = ""
        if ingredients:
            ingredient_data = "\n\nKnown ingredient nutritional data (per gram):\n"
            for ing in ingredients:
                ingredient_data += f"- {ing.name}: {ing.calories_per_gram:.2f} cal, {ing.protein_per_gram:.2f}g protein, {ing.fat_per_gram:.2f}g fat, {ing.carbs_per_gram:.2f}g carbs\n"
            add_content += ingredient_data
            add_content += "\n\nSearch other ingredients is they are not found in the list above."
        
        
        if user_settings and user_settings.macro_enabled:
            macro_text = f"\n\nMeal composition must be {user_settings.protein_pct}% protein, {user_settings.carbs_pct}% carbs, {user_settings.fat_pct}% fat."
            user_message = user_message + macro_text

        
        if system_content:
            messages.append({
                "role": "system",
                "content": system_content
            })
        
        for msg in history:
            messages.append({
                "role": msg.role,
                "content": msg.content + (add_content if msg.role == "user" else "")
            })
        
        messages.append({
            "role": "user",
            "content": user_message + add_content
        })
        
        # Use native ollama chat API
        response = self.client.chat(
            model=self.settings.ollama_model,
            messages=messages,
        )
        
        return response["message"]["content"]
