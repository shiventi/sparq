from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set, Tuple


DATA_DIR = Path(__file__).resolve().parent / "json"


def _read_json(path: Path) -> Any:
	with path.open("r", encoding="utf-8") as handle:
		return json.load(handle)


def _normalize_spaces(value: str) -> str:
	return re.sub(r"\s+", " ", value.strip())


def normalize_course_code(value: str) -> str:
	value = value.replace("_", " ")
	value = re.sub(r"[^A-Z0-9 ]", " ", value.upper())
	value = _normalize_spaces(value)
	parts = value.split(" ")
	normalized_parts: List[str] = []
	for part in parts:
		match = re.match(r"^(\d+)([A-Z]*)$", part)
		if match:
			number = match.group(1).lstrip("0") or "0"
			suffix = match.group(2)
			normalized_parts.append(f"{number}{suffix}")
		else:
			normalized_parts.append(part)
	return " ".join(normalized_parts)


def course_code_to_slug(value: str) -> str:
	value = normalize_course_code(value)
	return value.replace(" ", "_")


def normalize_key(value: str) -> str:
	return re.sub(r"[^a-z0-9]", "", value.lower())


def parse_units(units: Any) -> float:
	if units is None:
		return 0.0
	if isinstance(units, (int, float)):
		return float(units)
	units_str = str(units).strip().lstrip("|&")
	if "-" in units_str:
		start, *_ = units_str.split("-")
		try:
			return float(start)
		except ValueError:
			return 0.0
	try:
		return float(units_str)
	except ValueError:
		return 0.0


def extract_course_number(code: str) -> Optional[int]:
	match = re.search(r"\d+", code)
	if not match:
		return None
	try:
		return int(match.group(0))
	except ValueError:
		return None


PASSING_GRADES = {"A", "A-", "B+", "B", "B-", "C+", "C", "C-", "CR", "P", "S"}


def is_passing_grade(grade: Optional[str]) -> bool:
	if not grade:
		return False
	grade = grade.strip().upper()
	if grade.isdigit():
		return int(grade) >= 70
	return grade in PASSING_GRADES


def strip_condition_suffix(token: str) -> str:
	token = token.strip()
	token = re.sub(r"MAJOR\:[^\s]+", "", token)
	token = token.split("WITH_")[0]
	token = token.split(":")[-1]
	token = token.replace("_", " ")
	token = _normalize_spaces(token)
	return token


def split_ge_ai(tokens: Iterable[str]) -> Tuple[List[str], List[str]]:
	ge_areas: List[str] = []
	ai_areas: List[str] = []
	for token in tokens:
		up = str(token).upper()
		ge_matches = re.findall(r"GE_AREA_[A-Z0-9]+", up)
		ge_areas.extend(ge_matches)
		simple_matches = re.findall(r"(?<![A-Z0-9])([1-6][A-C]?)(?![A-Z0-9])", up)
		for match in simple_matches:
			normalized = f"GE_AREA_{match}"
			if normalized not in ge_areas:
				ge_areas.append(normalized)
		ai_matches = re.findall(r"US\d+", up)
		ai_areas.extend(ai_matches)
	return ge_areas, ai_areas


@dataclass
class PrereqGroup:
	kind: str  # "ALL", "ANY", or "SINGLE"
	tokens: List[str] = field(default_factory=list)

	@property
	def course_tokens(self) -> List[str]:
		results: List[str] = []
		for group in self.course_option_groups():
			for code in group:
				if code not in results:
					results.append(code)
		return results

	def course_option_groups(self) -> List[List[str]]:
		groups: List[List[str]] = []
		for token in self.tokens:
			token_norm = strip_condition_suffix(token)
			codes = re.findall(r"[A-Z]{2,}\s?\d+[A-Z]*", token_norm)
			if not codes and re.search(r"[A-Z]{2,}\s?\d", token_norm):
				codes = [token_norm]
			if not codes:
				continue
			options: List[str] = []
			for code in codes:
				normalized = normalize_course_code(code)
				if normalized not in options:
					options.append(normalized)
			if options:
				groups.append(options)
		return groups


def parse_prerequisites(raw: Any) -> List[PrereqGroup]:
	if not raw:
		return []
	groups: List[PrereqGroup] = []

	def _append(group: List[str], kind: str) -> None:
		if not group:
			return
		if kind == "SINGLE" and len(group) > 1:
			kind = "ALL"
		groups.append(PrereqGroup(kind=kind, tokens=group.copy()))

	current: List[str] = []
	current_kind = "SINGLE"

	def process_item(item: Any) -> None:
		nonlocal current_kind, current
		if isinstance(item, list):
			# Nested grouping, treat as independent group
			nested = []
			nested_kind = "SINGLE"
			for entry in item:
				if isinstance(entry, str):
					if entry.startswith("||"):
						nested_kind = "ANY"
						nested.append(entry[2:])
					elif entry.startswith("&&"):
						nested_kind = "ALL"
						nested.append(entry[2:])
					else:
						nested.append(entry)
			_append(nested, nested_kind)
			return

		if not isinstance(item, str):
			return

		token_upper = item.upper()
		if " OR " in token_upper:
			options = [part.strip() for part in re.split(r"\bOR\b", item, flags=re.IGNORECASE) if part.strip()]
			_append(options, "ANY")
			return
		if " AND " in token_upper:
			options = [part.strip() for part in re.split(r"\bAND\b", item, flags=re.IGNORECASE) if part.strip()]
			_append(options, "ALL")
			return

		if item.startswith("||"):
			_append(current, current_kind)
			current_kind = "ANY"
			current = [item[2:]]
		elif item.startswith("&&"):
			_append(current, current_kind)
			current_kind = "ALL"
			current = [item[2:]]
		else:
			if not current:
				current_kind = "SINGLE"
			current.append(item)

	if isinstance(raw, list):
		for entry in raw:
			process_item(entry)
	else:
		process_item(raw)

	_append(current, current_kind)
	return groups


@dataclass
class CourseInfo:
	code: str
	name: str
	units: float
	ge_areas: List[str] = field(default_factory=list)
	prerequisites: List[PrereqGroup] = field(default_factory=list)
	corequisites: List[PrereqGroup] = field(default_factory=list)


@dataclass
class Completion:
	code: str
	title: str
	units: float
	source: str
	detail: str
	ge_areas: List[str] = field(default_factory=list)


SEMESTER_ORDER = {"Fall": 0, "Spring": 1, "Summer": 2, "Winter": 3}


@dataclass
class Requirement:
	identifier: str
	display_name: str
	requirement_type: str
	units: float
	ge_areas: List[str] = field(default_factory=list)
	ai_areas: List[str] = field(default_factory=list)
	course_slug: Optional[str] = None
	year: Optional[int] = None
	term_order: Optional[int] = None
	order_index: int = 0
	alternatives: List[str] = field(default_factory=list)

	def all_course_slugs(self) -> List[str]:
		slugs: List[str] = []
		if self.course_slug:
			slugs.append(self.course_slug)
		for alt in self.alternatives:
			if alt not in slugs:
				slugs.append(alt)
		return slugs


class StudentRecord:
	def __init__(self) -> None:
		self.completed_courses: Dict[str, Completion] = {}
		self.in_progress_courses: Set[str] = set()
		self.fulfilled_ge: Dict[str, str] = {}
		self.fulfilled_ai: Dict[str, str] = {}
		self._source_priority = {"SJSU": 3, "CC": 2, "AP": 1}

	def add_completion(
		self,
		code_slug: str,
		completion: Completion,
		ge_areas: Iterable[str],
		ai_areas: Iterable[str],
	) -> None:
		existing = self.completed_courses.get(code_slug)
		if existing:
			existing_priority = self._source_priority.get(existing.source, 0)
			new_priority = self._source_priority.get(completion.source, 0)
			if new_priority < existing_priority:
				return
		self.completed_courses[code_slug] = completion
		for area in ge_areas:
			self.fulfilled_ge.setdefault(area, completion.source)
		for area in ai_areas:
			self.fulfilled_ai.setdefault(area, completion.source)


class DataStore:
	def __init__(self, data_dir: Path = DATA_DIR) -> None:
		self.data_dir = data_dir
		self.course_catalog = self._load_course_catalog()
		self.ge_catalog = self._load_ge_catalog()
		self.ap_catalog = self._load_ap_catalog()
		self.american_institutions = self._load_american_institutions()
		self.major_index = self._build_major_index()
		self._roadmap_cache: Dict[str, List[Dict[str, Any]]] = {}
		self._cc_cache: Dict[str, Dict[str, Any]] = {}
		self._academic_catalog_cache: Dict[str, Dict[str, Any]] = {}

	def _load_course_catalog(self) -> Dict[str, CourseInfo]:
		catalog_path = self.data_dir / "all_sjsu_courses_with_ge.json"
		raw_catalog = _read_json(catalog_path)
		courses: Dict[str, CourseInfo] = {}
		for entry in raw_catalog:
			code_raw = entry.get("course_id")
			if not code_raw:
				continue
			code = normalize_course_code(code_raw)
			slug = course_code_to_slug(code)
			ge_areas = []
			for area in entry.get("ge_areas", []) or []:
				if isinstance(area, str):
					ge_areas.append(area.strip())
			prerequisites = parse_prerequisites(entry.get("prerequisites"))
			corequisites = parse_prerequisites(entry.get("corequisites"))
			courses[slug] = CourseInfo(
				code=code,
				name=entry.get("course_name", code),
				units=parse_units(entry.get("units")),
				ge_areas=ge_areas,
				prerequisites=prerequisites,
				corequisites=corequisites,
			)
		return courses

	def _load_ge_catalog(self) -> Dict[str, Dict[str, Any]]:
		ge_path = self.data_dir / "ge_courses.json"
		data = _read_json(ge_path)
		catalog: Dict[str, Dict[str, Any]] = {}
		for entry in data:
			areas = entry.get("area")
			if isinstance(areas, list):
				area_list = [area.strip() for area in areas]
			elif isinstance(areas, str):
				area_list = [areas.strip()]
			else:
				area_list = []
			for area in area_list:
				key = area.upper()
				catalog[key] = {
					"title": entry.get("title", area),
					"courses": entry.get("course", []),
					"units": parse_units(entry.get("units", 0)),
				}
		return catalog

	def _load_ap_catalog(self) -> Dict[str, Dict[str, Any]]:
		ap_path = self.data_dir / "ap_courses.json"
		entries = _read_json(ap_path)
		catalog: Dict[str, Dict[str, Any]] = {}
		for entry in entries:
			key_variants = {
				normalize_key(entry.get("name", "")),
				normalize_key(entry.get("code", "")),
			}
			for key in key_variants:
				if key:
					catalog[key] = entry
		return catalog

	def _load_american_institutions(self) -> Dict[str, Dict[str, Any]]:
		ai_path = self.data_dir / "american_institutions.json"
		entries = _read_json(ai_path)
		catalog: Dict[str, Dict[str, Any]] = {}
		for entry in entries:
			catalog[entry.get("code", "").upper()] = entry
		return catalog

	def _build_major_index(self) -> Dict[str, Dict[str, Any]]:
		majors_path = self.data_dir / "sjsu_majors.json"
		entries = _read_json(majors_path)
		index: Dict[str, Dict[str, Any]] = {}
		for entry in entries:
			name = entry.get("major")
			if not name:
				continue
			slug = self._major_to_slug(name)
			trimmed = name.split(",")[0]
			index[normalize_key(name)] = {"name": name, "slug": slug}
			index[normalize_key(trimmed)] = {"name": name, "slug": slug}
		return index

	def _major_to_slug(self, major: str) -> str:
		slug = major.strip().lower()
		slug = slug.replace("&", "&")
		slug = re.sub(r"[^a-z0-9,&]+", "_", slug)
		slug = re.sub(r"_+", "_", slug).strip("_")
		return slug + ".json"

	def resolve_major(self, major_name: str) -> Optional[Dict[str, Any]]:
		if not major_name:
			return None
		key = normalize_key(major_name)
		if key in self.major_index:
			return self.major_index[key]
		# Fallback: fuzzy startswith match
		for stored_key, metadata in self.major_index.items():
			if stored_key.startswith(key):
				return metadata
		return None

	def load_roadmap(self, major_name: str) -> List[Dict[str, Any]]:
		metadata = self.resolve_major(major_name)
		if not metadata:
			raise ValueError(f"Major '{major_name}' not found in catalog")
		slug = metadata["slug"]
		if slug in self._roadmap_cache:
			return self._roadmap_cache[slug]
		roadmap_path = self.data_dir / "roadmaps" / slug
		if not roadmap_path.exists():
			raise FileNotFoundError(f"Roadmap file not found for major '{major_name}'")
		raw = _read_json(roadmap_path)
		output = raw.get("output") if isinstance(raw, dict) else raw
		if not isinstance(output, list):
			raise ValueError(f"Unexpected roadmap format for '{major_name}'")
		self._roadmap_cache[slug] = output
		return output

	def load_cc_articulation(self, institution: str) -> Optional[Dict[str, Any]]:
		if not institution:
			return None
		key = normalize_key(institution)
		if key in self._cc_cache:
			return self._cc_cache[key]
		filename = re.sub(r"[^a-z0-9]+", "_", institution.lower()).strip("_") + ".json"
		path = self.data_dir / "community_college" / filename
		if not path.exists():
			return None
		data = _read_json(path)
		self._cc_cache[key] = data
		return data

	def load_academic_catalog(self, major_name: str) -> Optional[Dict[str, Any]]:
		"""Load the academic catalog JSON for a specific major"""
		if not major_name:
			return None
		metadata = self.resolve_major(major_name)
		if not metadata:
			return None
		slug = metadata["slug"]
		if slug in self._academic_catalog_cache:
			return self._academic_catalog_cache[slug]
		catalog_path = self.data_dir / "academic_catalog" / slug
		if not catalog_path.exists():
			return None
		data = _read_json(catalog_path)
		self._academic_catalog_cache[slug] = data
		return data


def build_student_record(student_profile: Dict[str, Any], datastore: DataStore) -> StudentRecord:
	record = StudentRecord()

	# Process SJSU courses
	for course in student_profile.get("sjsu_courses", []) or []:
		code = normalize_course_code(course.get("code", ""))
		slug = course_code_to_slug(code)
		status = (course.get("status") or "").lower()
		grade = course.get("grade")
		if status == "in progress":
			record.in_progress_courses.add(slug)
			continue
		if not is_passing_grade(grade):
			continue
		info = datastore.course_catalog.get(slug)
		ge_from_course, ai_from_course = split_ge_ai(info.ge_areas if info else [])
		record.add_completion(
			slug,
			Completion(
				code=code,
				title=course.get("title", info.name if info else code),
				units=info.units if info else parse_units(course.get("units", 3)),
				source="SJSU",
				detail="SJSU coursework",
				ge_areas=ge_from_course,
			),
			ge_from_course,
			ai_from_course,
		)

	# Process AP exams
	for exam in student_profile.get("ap_exams", []) or []:
		score = exam.get("score")
		if score is None or score < 3:
			continue
		key = normalize_key(exam.get("test", ""))
		ap_entry = datastore.ap_catalog.get(key)
		if not ap_entry:
			continue
		sjsu_courses = ap_entry.get("sjsu_courses", []) or []
		satisfies = ap_entry.get("satisfies", []) or []
		ge_areas: Set[str] = set()
		ai_areas: Set[str] = set()
		for satisfaction in satisfies:
			if not satisfaction:
				continue
			if isinstance(satisfaction, list):
				tokens = satisfaction
			else:
				tokens = [satisfaction]
			for token in tokens:
				area = token.upper().replace(" ", "_")
				if area.startswith("AREA"):
					ge_areas.add("GE_" + area)
				elif area.startswith("GE_"):
					ge_areas.add(area)
				elif area.startswith("US"):
					ai_areas.add(area)
		for course_group in sjsu_courses:
			if not course_group:
				continue
			for course_code in course_group:
				if not course_code or "ELECTIVE" in course_code.upper() or "NO CREDIT" in course_code.upper():
					continue
				normalized_code = normalize_course_code(course_code)
				slug = course_code_to_slug(normalized_code)
				info = datastore.course_catalog.get(slug)
				ge_from_course, ai_from_course = split_ge_ai(info.ge_areas if info else [])
				combined_ge = set(ge_from_course) | ge_areas
				combined_ai = set(ai_from_course) | ai_areas
				record.add_completion(
					slug,
					Completion(
						code=normalized_code,
						title=info.name if info else normalized_code,
						units=info.units if info else parse_units(ap_entry.get("units", 3)),
						source="AP",
						detail=f"AP Exam: {ap_entry.get('name')}",
						ge_areas=list(combined_ge),
					),
					list(combined_ge),
					list(combined_ai),
				)

	# Process Community College courses
	cc_courses = student_profile.get("cc_courses", []) or []
	by_institution: Dict[str, List[Dict[str, Any]]] = {}
	for course in cc_courses:
		institution = course.get("institution") or ""
		by_institution.setdefault(institution, []).append(course)

	for institution, courses in by_institution.items():
		articulation = datastore.load_cc_articulation(institution)
		if not articulation:
			continue
		catalog_by_code: Dict[str, Dict[str, Any]] = {}
		for section in articulation.get("output", []):
			for mapped in section.get("courses", []):
				sjsu_course = normalize_course_code(mapped.get("sjsu_course", ""))
				if not sjsu_course or sjsu_course == "NONE":
					continue
				slug = course_code_to_slug(sjsu_course)
				catalog_by_code.setdefault(slug, []).append(mapped.get("equivalents", []))

		student_cc = {normalize_course_code(c.get("code", "")): c for c in courses if is_passing_grade(c.get("grade"))}
		for slug, equivalent_groups in catalog_by_code.items():
			if slug in record.completed_courses:
				continue
			matched = False
			used_courses: List[str] = []
			for equivalents in equivalent_groups:
				if not equivalents:
					continue
				combos = []
				current: List[str] = []
				current_kind = "SINGLE"
				for item in equivalents:
					if item.startswith("||"):
						if current:
							combos.append((current_kind, current.copy()))
						current_kind = "ANY"
						current = [normalize_course_code(item[2:])]
					elif item.startswith("&&"):
						if current:
							combos.append((current_kind, current.copy()))
						current_kind = "ALL"
						current = [normalize_course_code(item[2:])]
					else:
						if not current:
							current_kind = "SINGLE"
						current.append(normalize_course_code(item))
				if current:
					combos.append((current_kind, current.copy()))

				for kind, requirements in combos:
					if not requirements or requirements[0] == "NONE":
						continue
					if kind == "ALL":
						if all(req in student_cc for req in requirements):
							used_courses = requirements
							matched = True
							break
					else:  # ANY or SINGLE
						for req in requirements:
							if req in student_cc:
								used_courses = [req]
								matched = True
								break
						if matched:
							break
				if matched:
					break

			if not matched:
				continue
			info = datastore.course_catalog.get(slug)
			ge_from_course, ai_from_course = split_ge_ai(info.ge_areas if info else [])
			record.add_completion(
				slug,
				Completion(
					code=info.code if info else slug.replace("_", " "),
					title=info.name if info else slug.replace("_", " "),
					units=info.units if info else 3.0,
					source="CC",
					detail=f"{institution}: {', '.join(used_courses)}",
					ge_areas=ge_from_course,
				),
				ge_from_course,
				ai_from_course,
			)

	return record


def _is_course_slug(name: str) -> bool:
	parts = name.split("_")
	if len(parts) < 2:
		return False
	subject = parts[0]
	if not subject.isalpha() or len(subject) < 2:
		return False
	catalog = parts[1]
	return bool(re.match(r"^\d", catalog))


def _parse_requirement_tokens(name: Any) -> Tuple[List[str], List[str]]:
	if isinstance(name, list):
		combined = " ".join(str(item) for item in name)
	else:
		combined = str(name)
	upper = combined.upper()
	ge_matches = re.findall(r"GE_AREA_[A-Z0-9]+", upper)
	ai_matches_raw = re.findall(r"US[_A-Z0-9]+", upper)
	ai_matches: List[str] = []
	for match in ai_matches_raw:
		digits = re.findall(r"\d", match)
		if not digits:
			continue
		for digit in digits:
			ai_matches.append(f"US{digit}")
	return ge_matches, ai_matches


def build_requirements(roadmap: Sequence[Dict[str, Any]]) -> List[Requirement]:
	requirements: List[Requirement] = []
	seen: Set[str] = set()
	for index, entry in enumerate(roadmap):
		raw_name = entry.get("name", "")
		if not raw_name:
			continue
		if isinstance(raw_name, list):
			tokens: List[str] = []
			for item in raw_name:
				if not isinstance(item, str):
					continue
				candidate = item[2:] if item.startswith(("||", "&&")) else item
				candidate = candidate.strip()
				if candidate:
					tokens.append(candidate)
			identifier_source = tokens[0] if tokens else ""
			display_name = " / ".join(token.replace("_", " ") for token in tokens) or str(raw_name)
			course_tokens = tokens.copy()
		else:
			identifier_source = str(raw_name)
			display_name = str(raw_name).replace("_", " ")
			course_tokens = [raw_name] if isinstance(raw_name, str) else []
		identifier = str(identifier_source or display_name)
		year = entry.get("year")
		semester = entry.get("semester")
		term_order = SEMESTER_ORDER.get(str(semester), 99)
		units = parse_units(entry.get("units"))
		ge_areas, ai_areas = _parse_requirement_tokens(raw_name)

		course_slugs: List[str] = []
		for token in course_tokens:
			if not isinstance(token, str):
				continue
			if _is_course_slug(token):
				slug = course_code_to_slug(normalize_course_code(token))
				if slug not in course_slugs:
					course_slugs.append(slug)
		if not course_slugs and isinstance(identifier_source, str) and _is_course_slug(identifier_source):
			slug = course_code_to_slug(normalize_course_code(identifier_source))
			course_slugs.append(slug)

		if course_slugs:
			course_slug = course_slugs[0]
			alternatives = course_slugs[1:]
			identifier = course_slug
			requirement_type = "course"
		elif ge_areas or ai_areas:
			course_slug = None
			alternatives = []
			requirement_type = "ge"
		elif isinstance(raw_name, str) and "elective" in raw_name.lower():
			course_slug = None
			alternatives = []
			requirement_type = "elective"
		else:
			course_slug = None
			alternatives = []
			requirement_type = "milestone"

		if requirement_type == "milestone":
			name_lower = display_name.lower()
			if "physical education" in name_lower:
				requirement_type = "activity"
			elif name_lower.startswith("ge upper division") or name_lower.startswith("upper division ge"):
				ge_tag = re.sub(r"[^A-Z0-9]+", "_", display_name.upper()).strip("_")
				if ge_tag:
					ge_areas = [ge_tag]
				requirement_type = "ge"

		# Avoid duplicating the same GE requirement multiple times
		unique_key = (
			requirement_type,
			course_slug or identifier,
			tuple(sorted(ge_areas)),
			tuple(sorted(ai_areas)),
			tuple(sorted(alternatives)) if course_slugs else tuple(),
		)
		if requirement_type in {"ge", "course"} and unique_key in seen:
			continue
		seen.add(unique_key)

		requirements.append(
			Requirement(
				identifier=identifier,
				display_name=display_name,
				requirement_type=requirement_type,
				units=units,
				ge_areas=ge_areas,
				ai_areas=ai_areas,
				course_slug=course_slug,
				year=year,
				term_order=term_order,
				order_index=index,
				alternatives=alternatives,
			)
		)

	return requirements


def evaluate_requirement(
	requirement: Requirement,
	record: StudentRecord,
	datastore: DataStore,
	academic_catalog: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
	result: Dict[str, Any] = {
		"identifier": requirement.identifier,
		"display_name": requirement.display_name,
		"type": requirement.requirement_type,
		"units": requirement.units,
		"ge_areas": requirement.ge_areas,
		"ai_areas": requirement.ai_areas,
		"status": "remaining",
		"source": None,
		"detail": None,
	}

	def _slug_to_display(slug: str) -> str:
		info = datastore.course_catalog.get(slug)
		return info.code if info else slug.replace("_", " ")
	
	def _get_major_specific_courses(requirement_name: str) -> Optional[List[str]]:
		"""Extract major-specific course options from academic catalog"""
		if not academic_catalog:
			return None
		
		catalog_data = academic_catalog.get("output", {})
		req_key = normalize_key(requirement_name)
		
		# Check optional_sequences (like Science Electives)
		optional_sequences = catalog_data.get("major_requirements", {}).get("optional_sequences", [])
		for seq in optional_sequences:
			seq_name = seq.get("name", "")
			seq_key = normalize_key(seq_name)
			
			# Direct match
			if seq_key == req_key:
				courses = []
				for option_group in seq.get("options", []):
					for option in option_group:
						course_code = option.lstrip("|&").strip()
						if course_code and course_code != "NONE":
							courses.append(course_code)
				if courses:
					return courses
			
			# Special case: GE Area 5B/5C maps to Science Electives
			# Only match if requirement explicitly mentions 5b or 5c or is just "science"
			if "science" in seq_key and ("5b" in req_key or "5c" in req_key):
				courses = []
				for option_group in seq.get("options", []):
					for option in option_group:
						course_code = option.lstrip("|&").strip()
						if course_code and course_code != "NONE":
							courses.append(course_code)
				if courses:
					return courses
		
		# Check field_requirements (like Major Electives)
		field_requirements = catalog_data.get("field_requirements", [])
		for field in field_requirements:
			field_name = field.get("field_name", "")
			field_key = normalize_key(field_name)
			
			# For electives, check if the field name matches
			# "Computer Science Elective" should match "Major Electives" if it contains CS courses
			if field_key == req_key:
				courses = field.get("courses", [])
				if courses:
					return courses
			
			# Fuzzy match: "Computer Science Elective" or "Upper Division Computer Science Elective" 
			# should match field that has "Major Electives" and contains CS courses
			if "elective" in req_key and "elective" in field_key:
				courses = field.get("courses", [])
				# Check if this is a CS major electives field (has CS courses)
				if courses and any(c.startswith("CS ") for c in courses[:5] if isinstance(c, str)):
					# Only match if requirement mentions "computer" or "cs" or is generic "elective"
					if "computer" in req_key or "cs" in req_key or req_key == "elective":
						return courses
		
		return None

	if requirement.requirement_type == "course":
		course_slugs = requirement.all_course_slugs()
		for slug in course_slugs:
			completion = record.completed_courses.get(slug)
			if completion:
				result.update(
					{
						"status": "fulfilled",
						"source": completion.source,
						"detail": completion.detail,
						"title": completion.title,
						"units": completion.units or requirement.units,
						"satisfied_by": _slug_to_display(slug),
					}
				)
				if requirement.alternatives:
					result["alternatives"] = [_slug_to_display(alt) for alt in requirement.alternatives]
				return result
		for slug in course_slugs:
			if slug in record.in_progress_courses:
				info = datastore.course_catalog.get(slug)
				result.update(
					{
						"status": "in_progress",
						"detail": "Currently in progress",
						"title": info.name if info else requirement.display_name,
						"selected_course": _slug_to_display(slug),
					}
				)
				if requirement.alternatives:
					result["alternatives"] = [
						_slug_to_display(alt) for alt in requirement.alternatives if alt != slug
					]
				return result
		for slug in course_slugs:
			info = datastore.course_catalog.get(slug)
			if not info:
				continue
			prereq_strings: List[str] = []
			for group in info.prerequisites:
				options = group.course_option_groups()
				if not options:
					continue
				effective_kind = group.kind
				if effective_kind == "SINGLE" and (
					len(options) > 1 or (options and len(options[0]) > 1)
				):
					effective_kind = "ANY"
				display_segments = [
					" or ".join(code.replace("_", " ") for code in option) for option in options
				]
				if not display_segments:
					continue
				if effective_kind == "ANY":
					prereq_strings.append(" OR ".join(display_segments))
				else:
					prereq_strings.append(" AND ".join(display_segments))
			result.update(
				{
					"title": info.name,
					"units": info.units or requirement.units,
					"prerequisites": prereq_strings,
					"preferred_course": _slug_to_display(slug),
				}
			)
			break
		if requirement.alternatives:
			result["alternatives"] = [_slug_to_display(alt) for alt in requirement.alternatives]
		return result

	if requirement.requirement_type == "ge":
		ge_ok = True
		ge_sources: Set[str] = set()
		for area in requirement.ge_areas or []:
			if area in record.fulfilled_ge:
				ge_sources.add(record.fulfilled_ge[area])
			else:
				ge_ok = False
		ai_ok = True
		if requirement.ai_areas:
			any_mode = "or" in requirement.display_name.lower()
			satisfied = [area for area in requirement.ai_areas if area in record.fulfilled_ai]
			if any_mode:
				ai_ok = bool(satisfied)
			else:
				ai_ok = len(satisfied) == len(requirement.ai_areas)
		if ge_ok and ai_ok:
			result.update(
				{
					"status": "fulfilled",
					"source": ", ".join(sorted(ge_sources)) if ge_sources else "Transfer",
					"detail": "Requirement satisfied",
				}
			)
		else:
			# First try to get major-specific courses
			major_courses = _get_major_specific_courses(requirement.display_name)
			if major_courses:
				result["suggested_courses"] = major_courses
			else:
				# Fall back to generic GE catalog
				ge_entry = requirement.ge_areas[0] if requirement.ge_areas else None
				ge_info = datastore.ge_catalog.get(ge_entry) if ge_entry else None
				if ge_info:
					result["suggested_courses"] = ge_info.get("courses", [])
			result.setdefault("units", requirement.units or 3.0)
			if requirement.ge_areas:
				ge_info = datastore.ge_catalog.get(requirement.ge_areas[0])
				if ge_info:
					result.setdefault("units", ge_info.get("units", requirement.units))
		return result

	if requirement.requirement_type == "elective":
		# Check if there are major-specific elective courses
		major_courses = _get_major_specific_courses(requirement.display_name)
		if major_courses:
			result.update(
				{
					"detail": "Work with advisor to choose an appropriate elective.",
					"suggested_courses": major_courses,
				}
			)
		else:
			result.update(
				{
					"detail": "Work with advisor to choose an appropriate elective.",
				}
			)
		return result

	if requirement.requirement_type == "activity":
		result.update(
			{
				"type": "activity",
				"detail": requirement.display_name,
			}
		)
		return result

	# Milestones or other requirements
	result.update(
		{
			"status": "informational",
			"detail": "Check with major advisor for milestone completion.",
		}
	)
	return result


def analyze_requirements(
	student_profile: Dict[str, Any],
	datastore: DataStore,
) -> Tuple[StudentRecord, List[Dict[str, Any]], List[Dict[str, Any]], List[Requirement]]:
	roadmap = datastore.load_roadmap(student_profile.get("major", ""))
	requirements = build_requirements(roadmap)
	record = build_student_record(student_profile, datastore)
	
	# Load academic catalog for major-specific course suggestions
	academic_catalog = datastore.load_academic_catalog(student_profile.get("major", ""))

	fulfilled: List[Dict[str, Any]] = []
	remaining: List[Dict[str, Any]] = []

	for requirement in requirements:
		status = evaluate_requirement(requirement, record, datastore, academic_catalog)
		if status["status"] == "fulfilled":
			fulfilled.append(status)
		elif status["status"] == "in_progress":
			fulfilled.append(status)
		elif status["status"] == "informational":
			fulfilled.append(status)
		else:
			remaining.append(status)

	return record, fulfilled, remaining, requirements


def _requirement_units(requirement: Requirement, datastore: DataStore) -> float:
	if requirement.requirement_type == "course" and requirement.course_slug:
		info = datastore.course_catalog.get(requirement.course_slug)
		if info and info.units:
			return info.units
		if requirement.alternatives:
			for alt in requirement.alternatives:
				alt_info = datastore.course_catalog.get(alt)
				if alt_info and alt_info.units:
					return alt_info.units
	if requirement.requirement_type == "ge" and requirement.ge_areas:
		ge_info = datastore.ge_catalog.get(requirement.ge_areas[0])
		if ge_info and ge_info.get("units"):
			return float(ge_info["units"])
	return requirement.units or 3.0


def _prerequisites_satisfied(
	course_slug: str,
	completed: Set[str],
	required_slugs: Set[str],
	datastore: DataStore,
) -> bool:
	info = datastore.course_catalog.get(course_slug)
	if not info or not info.prerequisites:
		return True
	for group in info.prerequisites:
		option_groups = group.course_option_groups()
		if not option_groups:
			continue

		def _options_to_slugs(options: List[str]) -> List[str]:
			slugs: List[str] = []
			for option in options:
				slug = course_code_to_slug(option)
				if slug in datastore.course_catalog or slug in completed or slug in required_slugs:
					if slug not in slugs:
						slugs.append(slug)
			return slugs

		effective_kind = group.kind
		if effective_kind == "SINGLE" and (
			len(option_groups) > 1 or (option_groups and len(option_groups[0]) > 1)
		):
			effective_kind = "ANY"

		group_references_program = False

		if effective_kind == "ANY":
			references_program = False
			satisfied = False
			for options in option_groups:
				slugs = _options_to_slugs(options)
				if not slugs:
					continue
				if any(slug in required_slugs for slug in slugs):
					references_program = True
				if any(slug in completed for slug in slugs):
					satisfied = True
					break
			if references_program and not satisfied:
				return False
		else:  # ALL or SINGLE
			for options in option_groups:
				slugs = _options_to_slugs(options)
				if not slugs:
					continue
				if any(slug in required_slugs for slug in slugs):
					if not any(slug in completed for slug in slugs):
						return False
	return True


def plan_semesters(
	student_profile: Dict[str, Any],
	record: StudentRecord,
	requirements: List[Requirement],
	datastore: DataStore,
	academic_catalog: Optional[Dict[str, Any]] = None,
) -> Tuple[List[Dict[str, Any]], float]:
	units_per_semester = float(student_profile.get("units_per_semester") or 15)
	max_semester_units = units_per_semester
	
	def get_major_specific_courses(requirement_name: str) -> Optional[List[str]]:
		"""Extract major-specific course options from academic catalog"""
		if not academic_catalog:
			return None
		
		catalog_data = academic_catalog.get("output", {})
		req_key = normalize_key(requirement_name)
		
		# Check optional_sequences (like Science Electives)
		optional_sequences = catalog_data.get("major_requirements", {}).get("optional_sequences", [])
		for seq in optional_sequences:
			seq_name = seq.get("name", "")
			seq_key = normalize_key(seq_name)
			
			# Direct match
			if seq_key == req_key:
				courses = []
				for option_group in seq.get("options", []):
					for option in option_group:
						course_code = option.lstrip("|&").strip()
						if course_code and course_code != "NONE":
							courses.append(course_code)
				if courses:
					return courses
			
			# Special case: GE Area 5B/5C maps to Science Electives
			# Only match if requirement explicitly mentions 5b or 5c or is just "science"
			if "science" in seq_key and ("5b" in req_key or "5c" in req_key):
				courses = []
				for option_group in seq.get("options", []):
					for option in option_group:
						course_code = option.lstrip("|&").strip()
						if course_code and course_code != "NONE":
							courses.append(course_code)
				if courses:
					return courses
		
		# Check field_requirements (like Major Electives)
		field_requirements = catalog_data.get("field_requirements", [])
		for field in field_requirements:
			field_name = field.get("field_name", "")
			field_key = normalize_key(field_name)
			
			# For electives, check if the field name matches
			# "Computer Science Elective" should match "Major Electives" if it contains CS courses
			if field_key == req_key:
				courses = field.get("courses", [])
				if courses:
					return courses
			
			# Fuzzy match: "Computer Science Elective" or "Upper Division Computer Science Elective" 
			# should match field that has "Major Electives" and contains CS courses
			if "elective" in req_key and "elective" in field_key:
				courses = field.get("courses", [])
				# Check if this is a CS major electives field (has CS courses)
				if courses and any(c.startswith("CS ") for c in courses[:5] if isinstance(c, str)):
					# Only match if requirement mentions "computer" or "cs" or is generic "elective"
					if "computer" in req_key or "cs" in req_key or req_key == "elective":
						return courses
		
		return None

	def slug_to_display(slug: str) -> str:
		info = datastore.course_catalog.get(slug)
		return info.code if info else slug.replace("_", " ")

	def earliest_semester_index(req: Requirement) -> int:
		if req.year and req.year > 0:
			year_index = req.year - 1
		else:
			year_index = 0
		term_index = req.term_order if req.term_order is not None else 0
		if term_index >= 99:
			term_index = 0
		if term_index > 1:
			term_index = 1
		return max(0, year_index * 2 + term_index)

	def can_take_in_semester(req: Requirement, semester_idx: int) -> bool:
		roadmap_index = earliest_semester_index(req)
		if semester_idx >= roadmap_index:
			return True
		# Allow earlier scheduling when prerequisites are already satisfied by prior credit
		if req.requirement_type == "course":
			for slug in req.all_course_slugs():
				if slug in completed_prior:
					return False
				if _prerequisites_satisfied(slug, completed_prior, required_slugs, datastore):
					return True
			return False
		# GE, activities, and electives can be pulled forward if needed
		if req.requirement_type in {"ge", "activity", "elective"}:
			return True
		return False

	pending_courses = [
		req
		for req in requirements
		if req.requirement_type == "course"
		and req.all_course_slugs()
		and all(slug not in record.completed_courses for slug in req.all_course_slugs())
		and all(slug not in record.in_progress_courses for slug in req.all_course_slugs())
	]
	pending_ge = [
		req
		for req in requirements
		if req.requirement_type == "ge"
		and any(area not in record.fulfilled_ge for area in req.ge_areas)
	]
	pending_electives = [
		req
		for req in requirements
		if req.requirement_type == "elective"
	]
	pending_activities = [
		req
		for req in requirements
		if req.requirement_type == "activity"
	]

	def slug_is_upper_division(slug: str) -> bool:
		info = datastore.course_catalog.get(slug)
		if info and info.code:
			number = extract_course_number(info.code)
			if number is not None:
				return number >= 100
		# Fallback: parse from slug token
		parts = slug.split("_")
		if len(parts) > 1:
			number = extract_course_number(parts[1]) if parts[1] else None
			if number is not None:
				return number >= 100
		return False

	def requirement_is_upper_division(req: Requirement) -> bool:
		for slug in req.all_course_slugs():
			if slug_is_upper_division(slug):
				return True
		return False

	def requirement_is_upper_division_ge(req: Requirement) -> bool:
		"""Check if a GE requirement is upper-division"""
		name_lower = req.display_name.lower()
		return "upper division" in name_lower or "upper-division" in name_lower

	pending_courses.sort(
		key=lambda req: (
			requirement_is_upper_division(req),
			req.year or 99,
			req.term_order or 99,
			req.order_index,
		)
	)
	# Sort GE with lower-division first, then upper-division
	pending_ge.sort(key=lambda req: (
		requirement_is_upper_division_ge(req),
		req.year or 99,
		req.term_order or 99,
		req.order_index
	))
	pending_electives.sort(key=lambda req: (req.year or 99, req.term_order or 99, req.order_index))
	pending_activities.sort(key=lambda req: (req.year or 99, req.term_order or 99, req.order_index))

	total_units = sum(_requirement_units(req, datastore) for req in pending_courses)
	total_units += sum(_requirement_units(req, datastore) for req in pending_ge)
	total_units += sum(_requirement_units(req, datastore) for req in pending_electives)
	total_units += sum(_requirement_units(req, datastore) for req in pending_activities)
	initial_total_units = total_units
	completed_unit_total = sum((comp.units or 0.0) for comp in record.completed_courses.values())
	for slug in record.in_progress_courses:
		info = datastore.course_catalog.get(slug)
		if info and info.units:
			completed_unit_total += info.units
	scheduled_unit_total = 0.0
	MIN_UPPER_DIVISION_UNITS = 60.0

	completed_prior: Set[str] = set(record.completed_courses.keys()) | set(record.in_progress_courses)
	required_slugs: Set[str] = set()
	for req in requirements:
		if req.requirement_type == "course":
			for slug in req.all_course_slugs():
				required_slugs.add(slug)
	plan: List[Dict[str, Any]] = []
	semester_index = 0

	def lower_division_requirements_remaining() -> bool:
		for req in pending_courses:
			for slug in req.all_course_slugs():
				if not slug_is_upper_division(slug):
					return True
		return bool(pending_ge or pending_activities)

	def can_schedule_upper_division(slug: str) -> bool:
		if not slug_is_upper_division(slug):
			return True
		current_total = completed_unit_total + scheduled_unit_total
		if current_total >= MIN_UPPER_DIVISION_UNITS:
			return True
		return not lower_division_requirements_remaining()

	while pending_courses or pending_ge or pending_electives or pending_activities:
		term_label = f"Semester {semester_index + 1}"
		term_units = 0.0
		term_courses: List[Dict[str, Any]] = []
		term_completed: Set[str] = set()
		
		# Calculate how many courses are blocked by prerequisites
		# If we have many blocked courses, we should save electives for later
		blocked_courses = 0
		for req in pending_courses:
			if not can_take_in_semester(req, semester_index):
				continue
			available_slug = None
			for slug in req.all_course_slugs():
				if slug not in completed_prior:
					available_slug = slug
					break
			if available_slug and not _prerequisites_satisfied(available_slug, completed_prior, required_slugs, datastore):
				blocked_courses += 1
		
		# Schedule courses with satisfied prerequisites, filling semester to capacity
		# Keep trying to add courses, GE, and electives until we reach capacity or run out
		# PRIORITIZE lower-division GE courses early
		made_progress = True
		while made_progress and term_units < max_semester_units - 0.5:
			made_progress = False
			
			# FIRST: Try to add lower-division GE courses (these should be done early)
			for ge_req in list(pending_ge):
				if term_units >= max_semester_units - 0.5:
					break
				if not can_take_in_semester(ge_req, semester_index):
					continue
				# Only schedule lower-division GE in this phase
				if requirement_is_upper_division_ge(ge_req):
					continue
				ge_units = _requirement_units(ge_req, datastore)
				if term_units + ge_units <= max_semester_units:
					pending_ge.remove(ge_req)
					# Get major-specific courses or fall back to GE catalog
					suggested = get_major_specific_courses(ge_req.display_name)
					if not suggested and ge_req.ge_areas:
						suggested = datastore.ge_catalog.get(ge_req.ge_areas[0], {}).get("courses", [])
					term_courses.append(
						{
							"course": ge_req.display_name,
							"title": "Select approved GE course",
							"units": ge_units,
							"type": "ge",
							"suggested_courses": suggested or [],
						}
					)
					term_units += ge_units
					scheduled_unit_total += ge_units
					total_units -= ge_units
					made_progress = True
			
			# SECOND: Try to add lower-division courses with satisfied prerequisites
			for req in list(pending_courses):
				if not can_take_in_semester(req, semester_index):
					continue
				if term_units >= max_semester_units - 0.5:
					break
				# Prioritize lower-division courses in early semesters
				if requirement_is_upper_division(req) and lower_division_requirements_remaining():
					continue
				available_slug = None
				for slug in req.all_course_slugs():
					if slug not in completed_prior and slug not in term_completed:
						available_slug = slug
						break
				if not available_slug:
					continue
				if not _prerequisites_satisfied(available_slug, completed_prior, required_slugs, datastore):
					continue
				if not can_schedule_upper_division(available_slug):
					continue
				info = datastore.course_catalog.get(available_slug)
				course_units = info.units if info and info.units else max(req.units, 3.0)
				if term_units + course_units > max_semester_units:
					continue
				entry = {
					"course": info.code if info else slug_to_display(available_slug),
					"title": info.name if info else req.display_name,
					"units": course_units,
					"type": "course",
				}
				if req.alternatives:
					entry["alternatives"] = [
						slug_to_display(alt) for alt in req.alternatives if alt != available_slug
					]
				term_courses.append(entry)
				term_units += course_units
				scheduled_unit_total += course_units
				total_units -= course_units
				term_completed.add(available_slug)
				pending_courses.remove(req)
				made_progress = True
			
			# THIRD: Now try upper-division GE if we have space and met the 60-unit threshold
			current_total = completed_unit_total + scheduled_unit_total
			if current_total >= MIN_UPPER_DIVISION_UNITS:
				for ge_req in list(pending_ge):
					if term_units >= max_semester_units - 0.5:
						break
					if not can_take_in_semester(ge_req, semester_index):
						continue
					# Only upper-division GE in this phase
					if not requirement_is_upper_division_ge(ge_req):
						continue
					ge_units = _requirement_units(ge_req, datastore)
					if term_units + ge_units <= max_semester_units:
						pending_ge.remove(ge_req)
						# Get major-specific courses or fall back to GE catalog
						suggested = get_major_specific_courses(ge_req.display_name)
						if not suggested and ge_req.ge_areas:
							suggested = datastore.ge_catalog.get(ge_req.ge_areas[0], {}).get("courses", [])
						term_courses.append(
							{
								"course": ge_req.display_name,
								"title": "Select approved GE course",
								"units": ge_units,
								"type": "ge",
								"suggested_courses": suggested or [],
							}
						)
						term_units += ge_units
						scheduled_unit_total += ge_units
						total_units -= ge_units
						made_progress = True

			# Schedule short activity requirements (e.g., Physical Education)
			# Loop through ALL activities to pack the semester
			for activity_req in list(pending_activities):
				if term_units >= max_semester_units - 0.5:
					break
				if not can_take_in_semester(activity_req, semester_index):
					continue
				activity_units = _requirement_units(activity_req, datastore)
				if term_units + activity_units <= max_semester_units:
					pending_activities.remove(activity_req)
					entry = {
						"course": activity_req.display_name,
						"title": activity_req.display_name,
						"units": activity_units,
						"type": "activity",
					}
					term_courses.append(entry)
					term_units += activity_units
					scheduled_unit_total += activity_units
					total_units -= activity_units
					made_progress = True
			
			# After trying courses and GE, try electives if we still have space
			# Loop through ALL electives to pack the semester - don't create light semesters if we can avoid it
			# But leave room for blocked required courses AND don't over-schedule electives
			electives_target = max_semester_units
			blocked_required_count = sum(1 for req in pending_courses 
				if not any(_prerequisites_satisfied(slug, completed_prior, required_slugs, datastore) 
					for slug in req.all_course_slugs() if slug not in completed_prior))
			
			# Calculate how many electives we should schedule this semester
			# Strategy: distribute electives evenly across remaining semesters
			remaining_elective_units = sum(_requirement_units(req, datastore) for req in pending_electives)
			remaining_required_units = sum(_requirement_units(req, datastore) for req in pending_courses)
			total_remaining = remaining_elective_units + remaining_required_units + sum(_requirement_units(req, datastore) for req in pending_ge) + sum(_requirement_units(req, datastore) for req in pending_activities)
			
			if total_remaining > 0 and remaining_elective_units > 0:
				# Estimate semesters needed
				semesters_ahead = max(1, math.ceil(total_remaining / max_semester_units))
				electives_per_semester = remaining_elective_units / semesters_ahead
				electives_this_semester = min(remaining_elective_units, max(electives_per_semester, 3))
				electives_target = min(max_semester_units, term_units + electives_this_semester)
			
			if blocked_required_count > 0:
				# Leave extra room for blocked courses
				reserve_units = min(blocked_required_count * 3, 6)
				electives_target = min(electives_target, max(12, max_semester_units - reserve_units))
			
			for elective_req in list(pending_electives):
				if term_units >= electives_target - 0.5:
					break
				if not can_take_in_semester(elective_req, semester_index):
					continue
				elective_units = _requirement_units(elective_req, datastore)
				if term_units + elective_units <= electives_target:
					pending_electives.remove(elective_req)
					# Get major-specific elective courses
					suggested = get_major_specific_courses(elective_req.display_name)
					elective_entry = {
						"course": elective_req.display_name,
						"title": elective_req.display_name,
						"units": elective_units,
						"type": "elective",
						"detail": "Work with advisor to choose an appropriate elective.",
					}
					if suggested:
						elective_entry["suggested_courses"] = suggested
					term_courses.append(elective_entry)
					term_units += elective_units
					scheduled_unit_total += elective_units
					total_units -= elective_units
					made_progress = True

		# If we have space remaining in the semester, try to add blocked courses with prerequisite notes
		# This prevents creating many small semesters at the end
		if term_courses and term_units < max_semester_units - 0.5 and pending_courses:
			for idx in range(len(pending_courses) - 1, -1, -1):  # Work backwards to try blocked courses
				if term_units >= max_semester_units - 0.5:
					break
					
				fallback = pending_courses[idx]
				if not can_take_in_semester(fallback, semester_index):
					continue
					
				fallback_slug = None
				for slug in fallback.all_course_slugs():
					if slug not in completed_prior and slug not in term_completed:
						fallback_slug = slug
						break
				if not fallback_slug:
					continue
				
				# Check if prerequisites are satisfied (if not, we'll add a note)
				prereqs_ok = _prerequisites_satisfied(fallback_slug, completed_prior, required_slugs, datastore)
				
				# If prereqs are satisfied, this should have been scheduled in main loop - skip it
				if prereqs_ok:
					continue
				
				info = datastore.course_catalog.get(fallback_slug) if fallback_slug else None
				course_units = info.units if info and info.units else max(fallback.units, 3.0)
				
				if not can_schedule_upper_division(fallback_slug):
					continue
				
				# Check if adding this would overfill
				if term_units + course_units > max_semester_units:
					continue
				
				pending_courses.pop(idx)
				entry = {
					"course": info.code if info else slug_to_display(fallback_slug),
					"title": info.name if info else fallback.display_name,
					"units": course_units,
					"type": "course",
					"note": "Prerequisite data missing; verify with advisor.",
				}
				if fallback.alternatives:
					entry["alternatives"] = [
						slug_to_display(alt) for alt in fallback.alternatives if alt != fallback_slug
					]
				term_courses.append(entry)
				term_units += course_units
				scheduled_unit_total += course_units
				total_units -= course_units
				if fallback_slug:
					term_completed.add(fallback_slug)

		while term_units < max_semester_units - 0.5 and pending_activities:
			activity_req = None
			for candidate in pending_activities:
				if can_take_in_semester(candidate, semester_index):
					activity_req = candidate
					break
			if not activity_req:
				break
			activity_units = _requirement_units(activity_req, datastore)
			if term_units + activity_units > max_semester_units:
				break
			pending_activities.remove(activity_req)
			term_courses.append(
				{
					"course": activity_req.display_name,
					"title": activity_req.display_name,
					"units": activity_units,
					"type": "activity",
				}
			)
			term_units += activity_units
			scheduled_unit_total += activity_units
			total_units -= activity_units

		if not term_courses:
			# Deadlock: schedule pending courses ignoring prerequisites
			# Try to fill the semester with multiple deadlocked courses + electives
			# instead of creating many 3-unit semesters
			added_any = False
			while term_units < max_semester_units - 0.5 and pending_courses:
				fallback = pending_courses[0]
				if not can_take_in_semester(fallback, semester_index):
					break
				fallback_slug = None
				for slug in fallback.all_course_slugs():
					if slug not in completed_prior and slug not in term_completed:
						fallback_slug = slug
						break
				if fallback_slug and not can_schedule_upper_division(fallback_slug):
					break
				fallback = pending_courses.pop(0)
				info = datastore.course_catalog.get(fallback_slug) if fallback_slug else None
				course_units = info.units if info and info.units else max(fallback.units, 3.0)
				
				# Check if adding this would overfill
				if term_units + course_units > max_semester_units:
					# Put it back for next semester
					pending_courses.insert(0, fallback)
					break
					
				entry = {
					"course": info.code if info else slug_to_display(fallback_slug) if fallback_slug else fallback.display_name,
					"title": info.name if info else fallback.display_name,
					"units": course_units,
					"type": "course",
					"note": "Prerequisite data missing; verify with advisor.",
				}
				if fallback.alternatives:
					entry["alternatives"] = [
						slug_to_display(alt) for alt in fallback.alternatives if alt != fallback_slug
					]
				term_courses.append(entry)
				term_units += course_units
				scheduled_unit_total += course_units
				total_units -= course_units
				if fallback_slug:
					term_completed.add(fallback_slug)
				added_any = True
			
			# After adding deadlocked courses, fill up the semester with GE/electives
			while term_units < max_semester_units - 0.5 and pending_ge:
				ge_req = pending_ge[0]
				if not can_take_in_semester(ge_req, semester_index):
					break
				ge_units = _requirement_units(ge_req, datastore)
				if term_units + ge_units > max_semester_units:
					break
				pending_ge.pop(0)
				# Get major-specific courses or fall back to GE catalog
				suggested = get_major_specific_courses(ge_req.display_name)
				if not suggested and ge_req.ge_areas:
					suggested = datastore.ge_catalog.get(ge_req.ge_areas[0], {}).get("courses", [])
				term_courses.append(
					{
						"course": ge_req.display_name,
						"title": "Select approved GE course",
						"units": ge_units,
						"type": "ge",
						"suggested_courses": suggested or [],
					}
				)
				term_units += ge_units
				scheduled_unit_total += ge_units
				total_units -= ge_units

			while term_units < max_semester_units - 0.5 and pending_activities:
				activity_req = pending_activities[0]
				if not can_take_in_semester(activity_req, semester_index):
					break
				activity_units = _requirement_units(activity_req, datastore)
				if term_units + activity_units > max_semester_units:
					break
				pending_activities.pop(0)
				term_courses.append(
					{
						"course": activity_req.display_name,
						"title": activity_req.display_name,
						"units": activity_units,
						"type": "activity",
					}
				)
				term_units += activity_units
				scheduled_unit_total += activity_units
				total_units -= activity_units
			
			while term_units < max_semester_units - 0.5 and pending_electives:
				elective_req = pending_electives[0]
				if not can_take_in_semester(elective_req, semester_index):
					break
				elective_units = _requirement_units(elective_req, datastore)
				if term_units + elective_units > max_semester_units:
					break
				pending_electives.pop(0)
				# Get major-specific elective courses
				suggested = get_major_specific_courses(elective_req.display_name)
				elective_entry = {
					"course": elective_req.display_name,
					"title": elective_req.display_name,
					"units": elective_units,
					"type": "elective",
					"detail": "Work with advisor to choose an appropriate elective.",
				}
				if suggested:
					elective_entry["suggested_courses"] = suggested
				term_courses.append(elective_entry)
				term_units += elective_units
				scheduled_unit_total += elective_units
				total_units -= elective_units
			
			# If still no courses (only GE/electives left), handle those
			if not term_courses:
				if pending_ge:
					while term_units < max_semester_units - 0.5 and pending_ge:
						ge_req = pending_ge[0]
						if not can_take_in_semester(ge_req, semester_index):
							break
						pending_ge.pop(0)
						ge_units = _requirement_units(ge_req, datastore)
						if term_units + ge_units > max_semester_units:
							pending_ge.insert(0, ge_req)
							break
						# Get major-specific courses or fall back to GE catalog
						suggested = get_major_specific_courses(ge_req.display_name)
						if not suggested and ge_req.ge_areas:
							suggested = datastore.ge_catalog.get(ge_req.ge_areas[0], {}).get("courses", [])
						term_courses.append(
							{
								"course": ge_req.display_name,
								"title": "Select approved GE course",
								"units": ge_units,
								"type": "ge",
								"suggested_courses": suggested or [],
							}
						)
						term_units += ge_units
						scheduled_unit_total += ge_units
						total_units -= ge_units
				elif pending_activities:
					while term_units < max_semester_units - 0.5 and pending_activities:
						activity_req = pending_activities[0]
						if not can_take_in_semester(activity_req, semester_index):
							break
						pending_activities.pop(0)
						activity_units = _requirement_units(activity_req, datastore)
						if term_units + activity_units > max_semester_units:
							pending_activities.insert(0, activity_req)
							break
						term_courses.append(
							{
								"course": activity_req.display_name,
								"title": activity_req.display_name,
								"units": activity_units,
								"type": "activity",
							}
						)
						term_units += activity_units
						scheduled_unit_total += activity_units
						total_units -= activity_units
				elif pending_electives:
					while term_units < max_semester_units - 0.5 and pending_electives:
						elective_req = pending_electives[0]
						if not can_take_in_semester(elective_req, semester_index):
							break
						pending_electives.pop(0)
						elective_units = _requirement_units(elective_req, datastore)
						if term_units + elective_units > max_semester_units:
							pending_electives.insert(0, elective_req)
							break
						# Get major-specific elective courses
						suggested = get_major_specific_courses(elective_req.display_name)
						elective_entry = {
							"course": elective_req.display_name,
							"title": elective_req.display_name,
							"units": elective_units,
							"type": "elective",
							"detail": "Work with advisor to choose an appropriate elective.",
						}
						if suggested:
							elective_entry["suggested_courses"] = suggested
						term_courses.append(elective_entry)
						term_units += elective_units
						scheduled_unit_total += elective_units
						total_units -= elective_units

		if not term_courses:
			# Nothing could be scheduled this term; advance to next semester without adding an empty term
			semester_index += 1
			continue

		plan.append(
			{
				"term": term_label,
				"courses": term_courses,
				"total_units": round(term_units, 1),
			}
		)
		semester_index += 1
		completed_prior.update(term_completed)

	# Consolidate light semesters at the end - move courses from underloaded semesters into earlier ones
	if plan and units_per_semester:
		min_reasonable_load = min(12, units_per_semester * 0.75)  # At least 12 units or 75% of target
		
		# Work backwards through the plan
		for i in range(len(plan) - 1, 0, -1):  # Start from last semester, go backwards (but not semester 0)
			current_sem = plan[i]
			if current_sem['total_units'] >= min_reasonable_load:
				continue  # This semester is fine
			
			# Try to move courses from this light semester into earlier semesters
			courses_to_redistribute = current_sem['courses'][:]
			current_sem['courses'] = []
			current_sem['total_units'] = 0
			
			for course in courses_to_redistribute:
				placed = False
				# Try to place in earlier semesters
				for j in range(i):
					target_sem = plan[j]
					if target_sem['total_units'] + course['units'] <= max_semester_units:
						target_sem['courses'].append(course)
						target_sem['total_units'] = round(target_sem['total_units'] + course['units'], 1)
						placed = True
						break
				
				# If we couldn't place it earlier, keep it here
				if not placed:
					current_sem['courses'].append(course)
					current_sem['total_units'] = round(current_sem['total_units'] + course['units'], 1)
		
		# Remove any empty semesters
		plan = [sem for sem in plan if sem['courses']]
		
		# Renumber semesters after consolidation
		for idx, sem in enumerate(plan):
			sem['term'] = f"Semester {idx + 1}"

	if units_per_semester:
		estimated_semesters = max(len(plan), math.ceil(initial_total_units / units_per_semester))
	else:
		estimated_semesters = len(plan)
	return plan, int(estimated_semesters)


def validate_semester_plan(
	plan: List[Dict[str, Any]],
	summary: Dict[str, Any],
	datastore: DataStore,
) -> List[Dict[str, Any]]:
	"""Validate that prerequisites are satisfied in the generated plan"""
	completed: Set[str] = set()
	issues: List[Dict[str, Any]] = []
	
	# Add already fulfilled courses to completed set
	for fulfilled_req in summary.get('fulfilled', []):
		if fulfilled_req.get('type') == 'course':
			fulfilled_identifier = fulfilled_req.get('identifier', '')
			# Identifier is already in MATH_30 format, which matches catalog keys
			completed.add(fulfilled_identifier)
	
	for sem_idx, semester in enumerate(plan):
		term = semester['term']
		for course in semester['courses']:
			if course['type'] != 'course':
				continue
				
			course_code = course['course']
			slug = course_code_to_slug(normalize_course_code(course_code))
			info = datastore.course_catalog.get(slug)
			
			if info and info.prerequisites:
				for group in info.prerequisites:
					option_groups = group.course_option_groups()
					if not option_groups:
						continue
					
					# For each prerequisite group, check if it's satisfied
					effective_kind = group.kind
					if effective_kind == "SINGLE" and (
						len(option_groups) > 1 or (option_groups and len(option_groups[0]) > 1)
					):
						effective_kind = "ANY"
					
					if effective_kind == "ANY":
						# At least one option must be satisfied
						group_satisfied = False
						for option_group in option_groups:
							option_satisfied = any(
								course_code_to_slug(normalize_course_code(prereq)) in completed 
								for prereq in option_group
							)
							if option_satisfied:
								group_satisfied = True
								break
						
						if not group_satisfied and 'note' not in course:
							issues.append({
								'semester': term,
								'course': course_code,
								'title': info.name,
								'missing_prereqs': [" or ".join(opt) for opt in option_groups],
								'type': 'prerequisite_violation'
							})
					else:  # ALL or SINGLE
						# All options must be satisfied
						for option_group in option_groups:
							option_satisfied = any(
								course_code_to_slug(normalize_course_code(prereq)) in completed 
								for prereq in option_group
							)
							if not option_satisfied and 'note' not in course:
								issues.append({
									'semester': term,
									'course': course_code,
									'title': info.name,
									'missing_prereqs': option_group,
									'type': 'prerequisite_violation'
								})
			
			completed.add(slug)
	
	return issues


def verify_unit_totals(
	summary: Dict[str, Any],
	plan: List[Dict[str, Any]],
) -> Dict[str, Any]:
	"""Verify unit calculations are correct"""
	planned_units = sum(sem['total_units'] for sem in plan)
	expected_units = summary['units_remaining']
	
	return {
		'planned_units': planned_units,
		'expected_units': expected_units,
		'match': abs(planned_units - expected_units) < 0.1,
		'difference': round(planned_units - expected_units, 1)
	}


def generate_validation_report(
	plan: List[Dict[str, Any]],
	requirements: List[Requirement],
	summary: Dict[str, Any],
	datastore: DataStore,
) -> str:
	"""Generate a human-readable validation report"""
	report: List[str] = []
	report.append("=" * 60)
	report.append("VALIDATION CHECKLIST")
	report.append("=" * 60)
	report.append("")
	report.append("Legend:")
	report.append("  [AP/CC/SJSU] = Already completed")
	report.append("  [Planned] = Scheduled in future semesters")
	report.append("")
	
	# 1. Check all required courses are included
	required_courses = [r for r in requirements if r.requirement_type == 'course']
	scheduled_courses: List[str] = []
	scheduled_course_slugs: Set[str] = set()
	
	for semester in plan:
		for course in semester['courses']:
			if course['type'] == 'course':
				scheduled_courses.append(course['course'])
				slug = course_code_to_slug(normalize_course_code(course['course']))
				scheduled_course_slugs.add(slug)
	
	report.append("\n1. Required Courses Coverage:")
	missing_courses = 0
	for req in required_courses:
		info = datastore.course_catalog.get(req.course_slug) if req.course_slug else None
		if info:
			# Check if scheduled in plan
			included = req.course_slug in scheduled_course_slugs
			
			# Check if already fulfilled (from fulfilled requirements)
			is_fulfilled = False
			fulfilled_source = ""
			for fulfilled_req in summary.get('fulfilled', []):
				if fulfilled_req.get('type') == 'course':
					# The identifier in fulfilled is like "MATH_30", which matches req.course_slug
					fulfilled_identifier = fulfilled_req.get('identifier', '')
					
					if fulfilled_identifier == req.course_slug:
						is_fulfilled = True
						fulfilled_source = fulfilled_req.get('source', 'Fulfilled')
						break
					# Check if fulfilled via alternative
					if req.alternatives:
						for alt in req.alternatives:
							if fulfilled_identifier == alt:
								is_fulfilled = True
								fulfilled_source = fulfilled_req.get('source', 'Fulfilled')
								break
					if is_fulfilled:
						break
			
			# Check alternatives in the plan
			if not included and not is_fulfilled and req.alternatives:
				for alt in req.alternatives:
					if alt in scheduled_course_slugs:
						included = True
						break
			
			completed = included or is_fulfilled
			status = "✓" if completed else "✗"
			if not completed:
				missing_courses += 1
			
			# Show status with source
			if is_fulfilled:
				report.append(f"   {status} {info.code} - {info.name} [{fulfilled_source}]")
			elif included:
				report.append(f"   {status} {info.code} - {info.name} [Planned]")
			else:
				report.append(f"   {status} {info.code} - {info.name}")
	
	if missing_courses == 0:
		report.append("   ✓ All required courses are scheduled")
	else:
		report.append(f"   ⚠ {missing_courses} required course(s) missing from plan")
	
	# 2. Check semester loads
	report.append("\n2. Semester Unit Loads:")
	light_semesters = 0
	heavy_semesters = 0
	for semester in plan:
		units = semester['total_units']
		if units < 12:
			status = "⚠"
			light_semesters += 1
		elif units > 18:
			status = "⚠"
			heavy_semesters += 1
		else:
			status = "✓"
		report.append(f"   {status} {semester['term']}: {units} units")
	
	if light_semesters > 0:
		report.append(f"   ⚠ {light_semesters} semester(s) under 12 units (may affect financial aid)")
	if heavy_semesters > 0:
		report.append(f"   ⚠ {heavy_semesters} semester(s) over 18 units (may need approval)")
	
	# 3. Check for prerequisite violations
	report.append("\n3. Prerequisite Warnings:")
	prereq_issues = validate_semester_plan(plan, summary, datastore)
	flagged_courses = 0
	
	# First show courses with notes (expected issues)
	for semester in plan:
		for course in semester['courses']:
			if course.get('note') and 'Prerequisite' in course['note']:
				flagged_courses += 1
				report.append(f"   ⚠ {semester['term']}: {course['course']} - {course['note']}")
	
	# Then show unexpected prerequisite violations
	if prereq_issues:
		for issue in prereq_issues[:10]:  # Limit to first 10
			report.append(f"   ✗ {issue['semester']}: {issue['course']} ({issue['title']})")
			report.append(f"      Missing: {', '.join(issue['missing_prereqs'])}")
	
	if not prereq_issues and flagged_courses == 0:
		report.append("   ✓ No prerequisite violations detected")
	elif prereq_issues:
		report.append(f"   ✗ {len(prereq_issues)} unexpected prerequisite violation(s) found")
	
	# 4. Check unit totals
	report.append("\n4. Unit Calculations:")
	unit_check = verify_unit_totals(summary, plan)
	status = "✓" if unit_check['match'] else "✗"
	report.append(f"   {status} Planned units: {unit_check['planned_units']}")
	report.append(f"   {status} Expected units: {unit_check['expected_units']}")
	if not unit_check['match']:
		report.append(f"   ✗ Difference: {unit_check['difference']} units")
	
	# 5. Check for duplicate courses
	report.append("\n5. Duplicate Course Check:")
	course_counts: Dict[str, int] = {}
	for semester in plan:
		for course in semester['courses']:
			if course['type'] == 'course':
				course_counts[course['course']] = course_counts.get(course['course'], 0) + 1
	
	duplicates = [course for course, count in course_counts.items() if count > 1]
	if duplicates:
		for dup in duplicates:
			report.append(f"   ✗ {dup} scheduled {course_counts[dup]} times")
	else:
		report.append("   ✓ No duplicate courses found")
	
	# 6. Check GE requirements
	report.append("\n6. GE Requirements:")
	ge_reqs = [r for r in requirements if r.requirement_type == 'ge']
	scheduled_ge = sum(1 for sem in plan for c in sem['courses'] if c['type'] == 'ge')
	fulfilled_ge = len([r for r in summary.get('fulfilled', []) if r.get('type') == 'ge'])
	remaining_ge = len([r for r in summary.get('remaining', []) if r.get('type') == 'ge'])
	
	report.append(f"   • Total GE requirements: {len(ge_reqs)}")
	report.append(f"   • Fulfilled: {fulfilled_ge}")
	report.append(f"   • Scheduled: {scheduled_ge}")
	report.append(f"   • Remaining: {remaining_ge}")
	
	status = "✓" if remaining_ge == scheduled_ge else "⚠"
	report.append(f"   {status} GE coverage: {fulfilled_ge + scheduled_ge}/{len(ge_reqs)}")
	
	# 7. Check electives
	report.append("\n7. Elective Requirements:")
	elective_reqs = [r for r in requirements if r.requirement_type == 'elective']
	scheduled_electives = sum(1 for sem in plan for c in sem['courses'] if c['type'] == 'elective')
	
	report.append(f"   • Total elective requirements: {len(elective_reqs)}")
	report.append(f"   • Scheduled: {scheduled_electives}")
	
	status = "✓" if scheduled_electives == len(elective_reqs) else "⚠"
	report.append(f"   {status} Elective coverage: {scheduled_electives}/{len(elective_reqs)}")
	
	# Summary
	report.append("\n" + "=" * 60)
	report.append("RECOMMENDATION:")
	if not prereq_issues and missing_courses == 0 and unit_check['match'] and not duplicates:
		report.append("✓ Plan looks good! Review with your academic advisor.")
	else:
		report.append("⚠ Plan has some issues. Please review carefully with advisor.")
		report.append("  - Pay special attention to prerequisite warnings")
		report.append("  - Verify all required courses are included")
		report.append("  - Confirm elective selections with your department")
	report.append("=" * 60)
	
	return "\n".join(report)


def recommendation_engine(
	student_profile: Dict[str, Any],
	datastore: Optional[DataStore] = None,
) -> Tuple[Dict[str, Any], List[Dict[str, Any]], int]:
	datastore = datastore or DataStore()
	record, fulfilled, remaining, requirements = analyze_requirements(student_profile, datastore)
	
	# Load academic catalog for major-specific course suggestions
	academic_catalog = datastore.load_academic_catalog(student_profile.get("major", ""))
	
	plan, semesters = plan_semesters(student_profile, record, requirements, datastore, academic_catalog)

	units_remaining = sum(
		_requirement_units(req, datastore)
		for req in requirements
		if req.requirement_type == "course"
		and req.all_course_slugs()
		and all(slug not in record.completed_courses for slug in req.all_course_slugs())
		and all(slug not in record.in_progress_courses for slug in req.all_course_slugs())
	)
	units_remaining += sum(
		_requirement_units(req, datastore)
		for req in requirements
		if req.requirement_type == "ge"
		and any(area not in record.fulfilled_ge for area in req.ge_areas)
	)
	units_remaining += sum(
		_requirement_units(req, datastore)
		for req in requirements
		if req.requirement_type == "activity"
	)

	plan_total_units = sum(term.get("total_units", 0.0) for term in plan)
	plan_length = len(plan)
	acceleration: Optional[Dict[str, Any]] = None
	units_per_semester = float(student_profile.get("units_per_semester") or 15)
	if plan_length > 1:
		required_load = math.ceil(plan_total_units / (plan_length - 1))
		if required_load > units_per_semester and required_load <= 16:
			acceleration = {
				"target_units": required_load,
				"new_term_count": plan_length - 1,
			}
	
	clarifications: List[str] = []
	low_load_term = next((term for term in plan if term.get("total_units", 0) < 12), None)
	if low_load_term:
		clarifications.append(
			f"{low_load_term.get('term')} is under 12 units. Confirm financial aid, housing, or any additional requirements."
		)
	if any(course.get("type") == "elective" for term in plan for course in term.get("courses", [])):
		clarifications.append("Elective placeholders need advisor-approved course selections.")
	if any(course.get("type") == "ge" for term in plan for course in term.get("courses", [])):
		clarifications.append("Verify GE selections satisfy SJSU-approved Area lists and any double-counting rules.")

	notes: List[str] = []
	if acceleration and plan_length:
		notes.append(
			f"If you can take {acceleration['target_units']} units per semester, you could finish in {acceleration['new_term_count']} semesters (instead of {plan_length})."
		)
	notes.extend(clarifications)

	summary = {
		"fulfilled": fulfilled,
		"remaining": remaining,
		"units_remaining": round(units_remaining, 1),
		"acceleration": acceleration,
		"clarifications": clarifications,
		"notes": notes,
	}
	
	# Generate validation report
	validation_report = generate_validation_report(plan, requirements, summary, datastore)
	summary['validation_report'] = validation_report
	
	return summary, plan, semesters


def _format_prerequisites_for_display(prereqs: Optional[Any]) -> str:
	if not prereqs:
		return "None"
	if isinstance(prereqs, list) and all(isinstance(group, str) for group in prereqs):
		return "; then ".join(prereqs)
	groups: List[str] = []
	if isinstance(prereqs, Iterable):
		for group in prereqs:
			if not group:
				continue
			if isinstance(group, (list, tuple)):
				options = [str(token).replace("_", " ") for token in group]
				joined = " or ".join(options)
				groups.append(joined)
			else:
				groups.append(str(group))
	if not groups:
		return "None"
	if len(groups) == 1:
		return groups[0]
	return "; then ".join(groups)


def _clean_suggested_courses(courses: Optional[List[str]], limit: int = 8) -> str:
	if not courses:
		return "-"
	cleaned: List[str] = []
	for course in courses:
		if not isinstance(course, str):
			continue
		cleaned.append(course.lstrip("|&"))
	if not cleaned:
		return "-"
	if len(cleaned) > limit:
		return ", ".join(cleaned[:limit]) + ", …"
	return ", ".join(cleaned)


def _format_requirement_line(req: Dict[str, Any]) -> str:
	title = req.get("display_name") or req.get("identifier")
	units = req.get("units") or "-"
	detail = req.get("title") or req.get("detail")
	parts = [f"• {title} ({units} units)"]
	if detail:
		parts.append(f"  {detail}")
	if req.get("source"):
		parts.append(f"  Source: {req['source']}")
	if req.get("prerequisites"):
		parts.append(f"  Prereqs: {_format_prerequisites_for_display(req['prerequisites'])}")
	if req.get("suggested_courses"):
		parts.append(f"  Suggested: {_clean_suggested_courses(req['suggested_courses'])}")
	if req.get("alternatives"):
		parts.append(f"  Alternatives: {', '.join(req['alternatives'])}")
	if req.get("note"):
		parts.append(f"  Note: {req['note']}")
	return "\n".join(parts)


def render_report(summary: Dict[str, Any], plan: List[Dict[str, Any]], semesters: int) -> str:
	lines: List[str] = []
	lines.append("================ Degree Progress Overview ================")
	lines.append(f"Units remaining: {summary.get('units_remaining', '-')}")
	lines.append(f"Estimated semesters: {semesters}")
	lines.append("")

	fulfilled = [req for req in summary.get("fulfilled", []) if req.get("status") == "fulfilled"]
	if fulfilled:
		lines.append("Fulfilled requirements (sample):")
		for req in fulfilled[:10]:
			lines.append(_format_requirement_line(req))
		if len(fulfilled) > 10:
			lines.append(f"  …and {len(fulfilled) - 10} more")
		lines.append("")

	remaining = summary.get("remaining", [])
	if remaining:
		lines.append("Remaining requirements:")
		courses = [req for req in remaining if req.get("type") == "course"]
		ge_reqs = [req for req in remaining if req.get("type") == "ge"]
		electives = [req for req in remaining if req.get("type") == "elective"]
		other = [req for req in remaining if req.get("type") not in {"course", "ge", "elective"}]
		if courses:
			lines.append("  Courses:")
			for req in courses:
				lines.append("  " + _format_requirement_line(req))
		if ge_reqs:
			lines.append("  GE / AI:")
			for req in ge_reqs:
				lines.append("  " + _format_requirement_line(req))
		if electives:
			lines.append("  Electives / Other Guided:")
			for req in electives:
				lines.append("  " + _format_requirement_line(req))
		if other:
			lines.append("  Other:")
			for req in other:
				lines.append("  " + _format_requirement_line(req))
		lines.append("")

	if plan:
		lines.append("Semester-by-semester plan:")
		for term in plan:
			term_header = f"{term.get('term', 'Term')} — {term.get('total_units', 0)} units"
			lines.append(term_header)
			for course in term.get("courses", []):
				course_line = f"  • {course.get('course')} ({course.get('units')} units)"
				if course.get("title") and course.get("title") != course.get("course"):
					course_line += f" – {course.get('title')}"
				lines.append(course_line)
				if course.get("alternatives"):
					lines.append(f"      Alternatives: {', '.join(course['alternatives'])}")
				if course.get("suggested_courses"):
					lines.append(f"      Suggested: {_clean_suggested_courses(course['suggested_courses'])}")
				if course.get("note"):
					lines.append(f"      Note: {course['note']}")
			lines.append("")

	notes = summary.get("notes") or []
	if notes:
		lines.append("Notes:")
		for note in notes:
			lines.append(f"- {note}")
		lines.append("")

	return "\n".join(line for line in lines if line is not None)


if __name__ == "__main__":
	sample_student = {
		"major": "Computer Science",
		
		"units_per_semester": 15,
	}

	summary, plan, semesters = recommendation_engine(sample_student)
	
	# Create JSON output
	output = {
		"major": sample_student["major"],
		"units_remaining": summary["units_remaining"],
		"estimated_semesters": semesters,
		"fulfilled_requirements": summary["fulfilled"],
		"remaining_requirements": summary["remaining"],
		"semester_plan": plan,
		"notes": summary.get("notes", []),
	}
	
	# Print JSON
	print(json.dumps(output, indent=2))

