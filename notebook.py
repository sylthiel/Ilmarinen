class Note:
    def __init__(self, name):
        self.text = ''
        self.name = name

    def edit_text(self, text):
        self.text = text

class Notebook:
    def __init__(self):
        self.notes = []
        self.tag_dictionary = {}
        # 'abc' : [note1 ,note 2, note 3]
        # search('abc') tag_dictionary['abc']

    def add_tags(self, note, tags):
        for tag in tags:
            if tag in self.tag_dictionary:
                self.tag_dictionary[tag].append(note)
            else:
                self.tag_dictionary[tag] = [note]

    def add_note(self, note):
        self.notes.append(note)


    def edit_note(self, note_name, new_text):
        pass

    def delete_note(self, note_name):
        for note in self.notes:
            if note.name == note_name:
                self.notes.remove(note)

        for tag in self.tag_dictionary:
            results = self.tag_dictionary[tag]
            for note in results:
                print(note)
                # ....
                # ...
                pass

    def search(self, tag):
        return self.tag_dictionary.get(tag)
        # returns a list of Notes or None


if __name__ == '__main__':
    new_notebook = Notebook()
    new_note = Note('Note 1')
    new_note.edit_text('abc')
    new_notebook.add_note(new_note)
    new_notebook.add_tags(new_note, ['vasya', 'abbbb'])
    found_notes = new_notebook.search('vasya')
    if found_notes is not None:
        for fn in found_notes:
            print(f"{fn.name} -> {fn.text}")

    print(new_notebook.tag_dictionary.keys())

    for key in new_notebook.tag_dictionary:
        print(key)