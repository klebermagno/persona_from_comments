from src.app import initialize_environment, PersonaUI

if __name__ == "__main__":
    initialize_environment()
    ui = PersonaUI()
    ui.create_interface().launch(share=False)
