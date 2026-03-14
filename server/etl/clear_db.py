import server.controllers.cities as ct
import server.controllers.states as st
import server.controllers.nations as nt
import server.controllers.natural_disasters as nd

MODELS = [
    ct.cities,
    st.states,
    nt.nations,
    nd.disasters,
]

def clear_db():
    num_deleted = 0
    for model in MODELS:
        old_count = model.count()
        for record in model.read().values():
            model.delete(record.get('_id'))
        new_count = model.count()
        num_deleted += (old_count - new_count)
    return num_deleted

if __name__ == '__main__':
    num_deleted = clear_db()
    print(num_deleted)
