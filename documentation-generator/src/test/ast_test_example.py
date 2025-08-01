class Greeter:
    """Greets people."""

    def say_hello(self, name):
        """Says hello."""
        print(f"Hello, {name}")

def say_goodbye(name):
    # """Says goodbye.""" # commented out to test if docstring is ignored in parser results in structure_comp.ipynb
    print(f"Goodbye, {name}")