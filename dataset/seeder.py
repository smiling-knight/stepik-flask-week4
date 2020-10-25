import json

from dataset.data import teachers, goals as goals_mapping
from app import Goal, Teacher, db


def seed():
    goal_models = [Goal(inner_name=k, name=v) for k, v in goals_mapping.items()]
    db.session.add_all(goal_models)

    for t in teachers:
        teacher = Teacher(
            name=t["name"],
            about=t["about"],
            rating=t["rating"],
            picture=t["picture"],
            price=t["price"],
            free=json.dumps(t["free"])
        )
        for g in t["goals"]:
            for g_model in goal_models:
                if g == g_model.inner_name:
                    teacher.goals.append(g_model)
        db.session.add(teacher)
    db.session.commit()
