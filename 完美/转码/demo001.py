class Student:
    def __init__(self):  # 两者之间的区别
        self.name = None
        self.score = None

    def print_score(self):
        print("%s score is %s" % (self.name, self.score))

    def classify_grades(self):
        if self.score >= 80:
            return "A"
        elif self.score >= 70:
            return "B"
        else:
            return "C"


student = Student()
student.name = "张三"
student.score = 90

student.print_score()
print(student.classify_grades())
