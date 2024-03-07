from google.cloud import translate_v2


def translate_text(text, target_language="fr"):
    # Initialize the translation client
    translate_client = translate_v2.Client()

    # Translate the text
    translation = translate_client.translate(text, target_language=target_language)

    # Return the translated text
    return translation["translatedText"]


if __name__ == "__main__":
    # Text to translate
    text_to_translate = "Hello, how are you?"

    # Target language (default is French)
    target_language = "fr"

    # Translate the text
    translated_text = translate_text(text_to_translate, target_language)

    # Print the translated text
    print("Original text:", text_to_translate)
    print("Translated text:", translated_text)
