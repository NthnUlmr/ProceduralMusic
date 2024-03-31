# <GPLv3_Header>
## - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# \copyright
#                    Copyright (c) 2024 Nathan Ulmer.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

# <\GPLv3_Header>

##
# \mainpage Procedural Music Generator
#
# \copydoc main.py

##
# \file main.py
#
# \author Nathan Ulmer
#
# \date \showdate "%A %d-%m-%Y"
#
# \brief A script for experimenting with procedural music generation in python. At the moment it generates a song as a
# piano melody in C major with corresponding harmony being a major tritone using an octave offset of the current melody note
# as the root. The melody tries to force itself to walk back towards middle c.
## \TODO The main problem with this at the moment is that there is no repitition. Repitition legitimizes. I think what this
# algorithm needs is to generate a few measures of melody and then to repeat and add variations on top. This sounds almost
# ideal for a genetic algorithm. The problem is how do you measure fitness???

import rtmidi
import time
import random
import math
import threading

Instruments = {
    "Piano":89,
}
def main():
    midiout = rtmidi.MidiOut()
    available_ports = midiout.get_ports()

    if available_ports:
        midiout.open_port(0)
    else:
        midiout.open_virtual_port("My virtual output")

    random.seed(69)

    root = 60#random.choice(range(60,72))

    maxLoops = 100
    count = 0

    with midiout:
        instrument = random.choice(list(Instruments.values()))
        melodyNote = Chord(midiout, [Note(root+12, 112)], 0)
        bpm = random.gauss(140.0,30.0)
        baseBeat = 1.0/4.0#random.choice([1.0,1.0/2.0,1.0/4.0,1.0/8.0])
        notesPerMeasure = random.randint(1,8)
        volume = 50
        chordThread = threading.Thread(target = print, args=("lmao",))
        melodyThread = threading.Thread(target = print, args=("lmao",))
        while(count < maxLoops):
            volume = random.gauss(50, 10)
            volume = min(max(volume,40),150)
            isMajor = random.choice([True,False])

            generate_nextMelody_note(midiout, melodyNote)
            #melodyNote.play(random.choice([1.0, 1.0 / 2.0, 1.0 / 4.0, 1.0 / 8.0]))

            root = melodyNote.notes[0].key + random.choice([0]) + random.choice([-2, -2, -1])*12
            if(isMajor):
                currentChord = generate_major_tritone(midiout, root, volume, instrument)
            else:
                currentChord = generate_minor_tritone(midiout, root, volume, instrument)
            melodyDuration = random.choice([2.0, 1.5, 1.0, 1.0 / 2.0, 1.0 / 4.0, 1.0 / 4.0, 1.0 / 8.0, 1.0 / 16.0]) * 60.0 / bpm / baseBeat
            chordDuration  = random.choice([4.0,3.0,2.0,1.5,1.0,1.0/2.0,1.0/4.0])*60.0/bpm / baseBeat

            if not (chordThread.is_alive()):
                chordThread = chordThread = threading.Thread(target = currentChord.play, args=(chordDuration,))
                chordThread.start()

            if not (melodyThread.is_alive()):
                melodyThread = threading.Thread(target = melodyNote.play, args=(melodyDuration,))
                melodyThread.start()
            #melodyThread.join()
            #chordThread.join()
            time.sleep(min(chordDuration,melodyDuration))
            count = count + 1





def generate_major_tritone(midiout, root, volume, instrument):
    notes = []
    MajorInterval = 4
    MinorInterval = 3
    notes.append(Note(root, volume))
    notes.append(Note(root + MajorInterval, volume))
    notes.append(Note(root + MajorInterval + MinorInterval, volume))
    return Chord(midiout, notes, instrument)

def generate_minor_tritone(midiout, root, volume, instrument):
    notes = []
    MajorInterval = 4
    MinorInterval = 3
    notes.append(Note(root, volume))
    notes.append(Note(root + MinorInterval, volume))
    notes.append(Note(root + MajorInterval + MinorInterval, volume))
    return Chord(midiout, notes, instrument)

def generate_nextMelody_note(midiout, currentNote):
    prevNote = currentNote.notes[0].key
    dir_to_middle_c = -1 * math.copysign(1, prevNote - 60)
    newNote = currentNote.notes[0].key + abs(math.floor(random.gauss(0.0, 4))) * dir_to_middle_c

    octaveRoot = math.floor(newNote/12) * 12
    #key root + 0, 2, 4, 5, 7, 9, 10, 11, 12 # force the melody to stay in c major

    while(not( (newNote - octaveRoot) in [0,2,4,5,7,9,10,11,12])):
        newNote = currentNote.notes[0].key + abs(math.floor(random.gauss(0.0, 4))) * dir_to_middle_c
        octaveRoot = math.floor(newNote / 12) * 12


    currentNote.notes = [Note(newNote, currentNote.notes[0].volume)]



class Note:
    def __init__(self, key, volume):
        self.key = key
        self.volume = volume



class Chord:
    def __init__(self, midiout, notes=[], instrument=Instruments["Piano"]):
        self.midiout = midiout
        self.notes = notes
        self.instrument = instrument

    def play(self,duration):
        set_instrument_msg = [0xC0, self.instrument]
        self.midiout.send_message(set_instrument_msg)

        for note in self.notes:
            play_msg = [0x90, note.key, note.volume]
            self.midiout.send_message(play_msg)

        time.sleep(duration)
        self.stop()

    def stop(self):
        for note in self.notes:
            play_msg = [0x90, note.key, 0]
            self.midiout.send_message(play_msg)


class ChordSequence:
    def __init__(self, midiout,chords=[], delays=[]):
        self.chords = chords
        self.delays = delays

    def play(self):
        for ii in range(len(self.chords)):
            self.chords[ii].play(self.delays[ii])


if __name__ == "__main__":
    main()

# <GPLv3_Footer>
################################################################################
#                      Copyright (c) 2024 Nathan Ulmer.
################################################################################
# <\GPLv3_Footer>