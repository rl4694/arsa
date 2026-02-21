import server.controllers.cities as ct
import server.controllers.states as st
import server.controllers.nations as nt
import server.controllers.natural_disasters as nd

if __name__ == '__main__':
    models = [
        ct.cities,
        st.states,
        nt.nations,
        nd.disasters,
    ]

    for model in models:
        old_count = model.count()
        for record in model.read().values():
            model.delete(record.get('_id'))
        new_count = model.count()
        print(f"Deleted: {old_count - new_count}")
