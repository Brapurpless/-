import sqlite3

# 连接到数据库
conn = sqlite3.connect('ai_teaching_platform.db')
c = conn.cursor()

# 查看所有表
print("数据库中的表:")
c.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = c.fetchall()
for table in tables:
    print(f"- {table[0]}")

# 查看users表结构
print("\nusers表结构:")
c.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='users'")
print(c.fetchone()[0])

# 查看users表数据
print("\nusers表数据:")
c.execute("SELECT * FROM users")
users = c.fetchall()
for user in users:
    print(user)

# 查看courses表结构
print("\ncourses表结构:")
c.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='courses'")
print(c.fetchone()[0])

# 查看courses表数据
print("\ncourses表数据:")
c.execute("SELECT * FROM courses")
courses = c.fetchall()
for course in courses:
    print(course)

# 查看lesson_plans表结构
print("\nlesson_plans表结构:")
c.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='lesson_plans'")
print(c.fetchone()[0])

# 查看lesson_plans表数据
print("\nlesson_plans表数据:")
c.execute("SELECT * FROM lesson_plans")
lessons = c.fetchall()
for lesson in lessons:
    print(lesson)

conn.close()