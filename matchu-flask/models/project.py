from sqlalchemy import Table, Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import mapper, relationship
from services.database import metadata, db_session
import datetime
import random
import json
import string
import time

def randomString(stringLength=10):
	"""Generate a random string of fixed length """
	letters = string.ascii_letters + string.digits
	return ''.join(random.choice(letters) for i in range(stringLength))

def compareSchedules(schedule1, schedule2):
	max_min_times = {}
	time_difference = {}
	total_hours = 0

	days = ["sun", "mon", "tue", "wed", "thu", "fri", "sat"]
	for i in range(7):
		day = days[i]
		sch1_day = [datetime.datetime.strptime(x, "%H:%M").hour for x in schedule1[day]] if day in schedule1 else [0, 0]
		sch2_day = [datetime.datetime.strptime(x, "%H:%M").hour for x in schedule2[day]] if day in schedule2 else [0, 0]

		if sch1_day	== [0, 0] or sch2_day == [0, 0]:
			continue

		day_starts = [sch1_day[0], sch2_day[0]]
		day_ends = [sch1_day[1], sch2_day[1]]


		max_min_times[days[i]] = ["{}:00".format(max(day_starts)), "{}:00".format(min(day_ends))]
		time_difference[i] = min(day_ends) - max(day_starts)
		if time_difference[i] < 0:
			time_difference[i] = 0

	for key in time_difference:
		total_hours += time_difference[key]

	if total_hours < 6:
		return False 
	else:
		return max_min_times, time_difference

	return max_min_times, time_difference


class Project(object):
	query = db_session.query_property()

	def __init__(self,  project_name, user_id, description, autoAssign_group_id = None):
		self.project_id = randomString(50)
		self.project_name = project_name
		self.user_id = user_id
		self.description = description
		self.groups = self.get_groups()
		self.nice_url = self.project_id[:8]

		self.autoAssign_group_id = autoAssign_group_id


	def get_groups(self):
		self.groups = Group.query.filter_by(project_id=self.project_id).order_by(Group.name.asc()).all()

		return self.groups
	
	def get_members(self):
		self.members = StudentToProject.query.filter_by(project_id=self.project_id).all()

		return self.members

	def assign_autoassign(self):
		print("hello world")
		autoAssign_group = Group.query.filter_by(id=self.autoAssign_group_id).first()

		no_place = []

		members = autoAssign_group.get_members()

		numberOfMembers = len(members)

		left_overs = numberOfMembers % 3
		max_groups = 3

		if max_groups in [0, 1]:
			groups = [members]

		else:

			groups = []

			while len(groups) <= max_groups and numberOfMembers >= 1:
				print("GROUPS", len(groups) <= max_groups, len(groups), max_groups)
				print("MEMBERS", numberOfMembers > 1, numberOfMembers)

				#print(len(groups), max_groups)
				group = []
				found_group = False
				# Loop each member
				for x in range(numberOfMembers):
					# get the current member
					member = members[x]
					print("Found Member: ", member)
					group.append(member)

					schedule = json.loads(member.schedule)

					for y in range(numberOfMembers):

						member2 = members[y]
						schedule2 = json.loads(member2.schedule)

						if member == member2:
							continue
						
						print("TESTING MEMBER 2:", member2)

						compare = compareSchedules(schedule, schedule2)

						if not compare is False:
							print("Found Member: ", member2)

							if not len(compare[0]) > 2:
								continue

							group.append(member2)
							new_schedule = compare[0]

							for z in range(numberOfMembers):
								member3 = members[z]

								if member3 == member2 or member3 == member:
									continue

								print("TESTING MEMBER 3:", member3)
								final_schedule = compareSchedules(new_schedule, json.loads(member3.schedule))

								if not final_schedule is False:
									print("Found Member: ", member3)
									group.append(member3)
									groups.append(group)
									found_group = True

									if numberOfMembers == 3:
										numberOfMembers = 0

									break
								
								if left_overs == 2:
									groups.append(group)
									left_overs = 0
									found_group = True
									break


							if len(group) == 3 or found_group:
								break


					if found_group:
						break
					elif len(group) < 3:
						print("no group")
						no_place.append(member)
						print(no_place)
						members.remove(member)
						numberOfMembers = len(members)
						break

				if found_group:
					for student in group:
						members.remove(student)
					
					numberOfMembers = len(members)
					if numberOfMembers == 3:
						groups.append(members)
						members = []
						break

				if len(groups) == max_groups and 1 <= len(no_place) <= 4:
					groups.append(no_place)
					no_place = []
					print("no_place reset")
					break

			if not no_place == []:
				if len(no_place) == 1 and len(groups[-1]) < 4:
					groups[-1].append(no_place[0])
				elif len(groups[-1]) >= 4:
					groups.append([no_place[0]])
				else:
					for i in range(0, len(no_place), 3):
						print("no place %s " % i, no_place[i:i + 3])
						groups.append(no_place[i:i + 3])

		rows_to_add = []
		for i, group in enumerate(groups, start=1):
			groupObj = Group("Group #%s" % (i), self.project_id, "Describe your project here!")
			try:
				db_session.add(groupObj)
				db_session.commit()
			except:
				db_session.rollback()
				return False

			for user in group:
				stu_to_group = StudentToGroup(group_id=groupObj.id, user_id=user.id)
				rows_to_add.append(stu_to_group)


		db_session.delete(autoAssign_group)
		db_session.commit()
		db_session.add_all(rows_to_add)
		self.autoAssign_group_id = None
		db_session.commit()

		try:
			db_session.delete(autoAssign_group)
			db_session.add_all(rows_to_add)
			self.autoAssign_group_id = None
			db_session.commit()
		except:
			db_session.rollback()
			return False
		else:
			return True


 
	def __repr__(self):
		return '<Project %r>' % (self.project_name)

projects = Table('projects', metadata,
	Column('project_id', String(80), primary_key=True, unique=True , index=True),
	Column('project_name', String(100)),
	Column('user_id', String(80), ForeignKey("users.id")),
	Column('description', Text()),
	Column('nice_url', String(8)),
	Column('autoAssign_group_id', String(5)),
	extend_existing=True
)
mapper(Project, projects)

from .group import Group
from .student_to_group import StudentToGroup
from .student_to_project import StudentToProject