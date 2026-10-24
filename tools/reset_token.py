import sqlite3

c = sqlite3.connect('C:/Users/yogen/.gemini/antigravity/scratch/lifecard/lifecard.db')
c.execute("UPDATE settings SET token='asha-demo-token'")
c.commit()
c.close()
print("Token reset successfully to asha-demo-token")
