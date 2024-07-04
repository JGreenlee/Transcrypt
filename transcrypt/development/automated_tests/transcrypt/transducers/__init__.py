
def run (autoTester):
    autoTester.check (list (filter (lambda x: x % 2 == 0, range (10))))

    autoTester.check (list (map (lambda x: x* x, range(0, 31, 3))))
    autoTester.check (list (map (lambda x, y: x * y, range(0, 31, 3), [1, 2, 3])))
    autoTester.check (list (map (lambda x, y, z: x * y + z, range(0, 31, 3), [1, 2, 3, 4], (2, 4, 6))))
