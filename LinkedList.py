def display(self):
    height = self.getHeight()
    for line in range(height):
        if self.leftchild is None and self.rightchild is None:
            print(self.value, end=' '*(2**line))
            return

        if self.leftchild is not None:
            self.leftchild.fillTree(x)
        if self.rightchild is not None:
            self.rightchild.fillTree(x)
