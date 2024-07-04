import itertools

class SerialGenerator:
    def __init__(self, start_value="FFFFFF00"):
        self.start_value = start_value
        self.serial_iterator = itertools.count(int(self.start_value, 16), 1)
        self.current_value = self.start_value

    def get_next_serial(self):
        self.current_value = f"{hex(next(self.serial_iterator))[2:].zfill(8)}"
        return self.current_value

    def __str__(self):
        return self.get_next_serial()

    @property
    def next_serial(self):
        return self.get_next_serial()

if __name__ == '__main__':
    # Example usage:
    generator = SerialGenerator(start_value="FFFFF000")
    this_bp = {'some_key': 'some_value'}

    this_bp_sn = this_bp.get('serial', generator.get_next_serial()) 
    print(this_bp_sn)  # Output: FFFFFF00

    this_bp_sn = this_bp.get('serial', generator.get_next_serial()) 
    print(this_bp_sn)  # Output: FFFFFF01

    this_bp_sn = this_bp.get('serial', generator.get_next_serial()) 
    print(this_bp_sn)  # Output: FFFFFF02

    print(generator)
    print(generator)
    print(generator)
    print(generator)
    print(generator)
    print(generator)
    print(generator)
    print(generator)
    print(generator)
    print(generator)
    print(generator)
    print(generator)
    print(generator)
    print(generator)
    print(generator)
    print(generator)
    print(generator)
    print(generator)
    print(generator)

    some_string_variable = generator.next_serial
    print(f'Warning!! Not updated!')
    print(some_string_variable)
    print(some_string_variable)
    print(some_string_variable)
    print(some_string_variable)
