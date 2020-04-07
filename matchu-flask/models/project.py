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
		self.groups = Group.query.filter_by(project_id=self.project_id).all()

		return self.groups
	


	def assign_autoassign(self):
		autoAssign_group = Group.query.filter_by(id=self.autoAssign_group_id).first()

		no_place = []

		members = autoAssign_group.get_members()
		print(members)

		numberOfMembers = len(members)

		left_overs = numberOfMembers % 3
		max_groups = numberOfMembers // 3

		if left_overs > 1:
			max_groups += 1


		groups = []

		while len(groups) != max_groups or numberOfMembers > 1:
			group = []
			found_group = False
			# Loop each member
			for x in range(numberOfMembers):
				print("FOUND X", x)
				# get the current member
				member = members[x]
				group.append(member)

				schedule = json.loads(member.schedule)

				for y in range(numberOfMembers):
					print("TESTING Y", y)
					if x == y:
						continue

					member2 = members[y]
					schedule2 = json.loads(member2.schedule)

					compare = compareSchedules(schedule, schedule2)

					if not compare is False:
						if not len(compare[0]) > 2:
							continue

						group.append(member2)
						new_schedule = compare[0]

						for z in range(numberOfMembers):
							print("TESTING Z", z)

							member3 = members[z]

							if member3 == member2 or member3 == member:
								continue

							final_schedule = compareSchedules(new_schedule, json.loads(member3.schedule))

							if not final_schedule is False:
								print("FOUND Z", z)

								print(final_schedule[0])
								group.append(member3)
								groups.append(group)
								found_group = True
								break
							
							if left_overs == 2:
								groups.append(group)
								print(new_schedule)
								left_overs = 0
								found_group = True
								break

						if len(group) == 3 or found_group:
							print("Found z, breaking")
							break


				if found_group:
					break

				if len(group) == 1:
					no_place.append(member)
					members.remove(member)
					numberOfMembers = len(members)
					break



			if found_group:
				print("FOUND GROUP:", group)
				print()
				for student in group:
					print(student)
					members.remove(student)
				
				numberOfMembers = len(members)
				if numberOfMembers == 3:
					groups.append(members)
					members = []
					break

		members = members + no_place
		left_overs += len(no_place)

		if not members == []:
			if len(members) == 1 and left_overs == 1:
				groups[-1].append(members[0])
			else:
				for i in range(0, len(members)):
					groups.append(members[i:i + 3])


		print(groups)

 
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