# seed.py
from database import SessionLocal
import models

def seed_data():
    db = SessionLocal()
    
    # 1. Виправлений перелік національностей (громадянство)
    nationalities_list = [
        "Українець / Українка", 
        "Поляк / Полька", 
        "Німець / Німкеня", 
        "Француз / Француженка", 
        "Англієць / Англійка", 
        "Американець / Американка", 
        "Канадієць / Канадійка", 
        "Чех / Чешка"
    ]
    
    print("Очищення та перезаповнення національностей...")
    
    # Видаляємо старі варіанти (країни), якщо вони були, щоб не було каші
    db.query(models.Nationality).delete()
    
    # Додаємо правильні національності
    for nat_name in nationalities_list:
        db.add(models.Nationality(name=nat_name))
            
    # Перевіряємо гендери
    db.query(models.Gender).delete()
    genders_list = ["Чоловік", "Жінка", "Віддаю перевагу не зазначати"]
    for gen_name in genders_list:
        db.add(models.Gender(name=gen_name))
            
    db.commit()
    db.close()
    print("Правильні національності та гендери успішно додано!")

if __name__ == "__main__":
    seed_data()