from icalendar import Calendar as iCalendar
from icalendar import Event as iEvent

from .event import Event as ZeusEvent


def to_ical(zevent: ZeusEvent) -> iEvent:
    """Converts a Zeus event to an ical Event (sub)object"""
    ievent = iEvent()
    ievent['uid'] = zevent.id
    ievent['summary'] = zevent.title  # FIXME: Moar words
    ievent['dtstart'] = zevent.date
    return ievent


def generate_calendar(ievents: list[iEvent]) -> iCalendar:
    """Aggregates given ical events into a calendar object"""
    cal = iCalendar()
    for ievent in ievents:
        cal.add_component(event)
    return cal


def create_ical_file(ical: iCalendar, filepath: str):
    with open(filepath, 'w') as ical_file:
        ical_file.write(ical.to_ical())
        ical_file.write("\n")  # End of file newline

if __name__ == '__main__':
     # Fetch a few zeus events, left up to the reader:
     # events: list[ZeusEvent] = magic_event_fetcher()
     zevents = []
     ievents = [to_ical(zevent) for zevent in in zevents]
     cal = generate_calendar(ievents)
     create_ical_file("zeus_events.ics")
