#!/usr/bin/env python
# -*- coding: latin-1 -*-
import atexit
import codecs
import csv
import random
from os.path import join

import yaml
from psychopy import visual, event, logging, gui, core

from misc.screen_misc import get_screen_res, get_frame_rate


@atexit.register
def save_beh_results():
    """
    Save results of experiment. Decorated with @atexit in order to make sure, that intermediate
    results will be saved even if interpreter will break.
    """
    with open(join('results', PART_ID + '_' + str(random.choice(range(100, 1000))) + '_beh.csv'), 'w',
              encoding='utf-8') as beh_file:
        beh_writer = csv.writer(beh_file)
        beh_writer.writerows(RESULTS)
    logging.flush()


def show_image(win, file_name, size, key='f7'):
    """
    Show instructions in a form of an image.
    """
    image = visual.ImageStim(win=win, image=file_name, interpolate=True, size=size)
    image.draw()
    win.flip()
    clicked = event.waitKeys(keyList=[key, 'return', 'space'])
    if clicked == [key]:
        logging.critical('Experiment finished by user! {} pressed.'.format(key[0]))
        exit(0)
    win.flip()


def read_text_from_file(file_name, insert=''):
    """
    Method that read message from text file, and optionally add some
    dynamically generated info.
    :param file_name: Name of file to read
    :param insert:
    :return: message
    """
    if not isinstance(file_name, str):
        logging.error('Problem with file reading, filename must be a string')
        raise TypeError('file_name must be a string')
    msg = list()
    with codecs.open(file_name, encoding='utf-8', mode='r') as data_file:
        for line in data_file:
            if not line.startswith('#'):  # if not commented line
                if line.startswith('<--insert-->'):
                    if insert:
                        msg.append(insert)
                else:
                    msg.append(line)
    return ''.join(msg)


def check_exit(key='f7'):
    """
    Check (during procedure) if experimentator doesn't want to terminate.
    """
    stop = event.getKeys(keyList=[key])
    if stop:
        abort_with_error('Experiment finished by user! {} pressed.'.format(key))


def show_info(win, file_name, insert=''):
    """
    Clear way to show info message into screen.
    :param win:
    :return:
    """
    msg = read_text_from_file(file_name, insert=insert)
    msg = visual.TextStim(win, color='black', text=msg, height=20, wrapWidth=SCREEN_RES['width'])
    msg.draw()
    win.flip()
    key = event.waitKeys(keyList=['f7', 'return', 'space', 'left', 'right'])
    if key == ['f7']:
        abort_with_error('Experiment finished by user on info screen! F7 pressed.')
    win.flip()


def abort_with_error(err):
    """
    Call if an error occured.
    """
    logging.critical(err)
    raise Exception(err)


# GLOBALS

RESULTS = list()  # list in which data will be collected
RESULTS.append(['PART_ID', 'block no', 'trial no', 'key pressed', 'reaction time', 'cars left right orientation',
                'middle car left right orientation', 'cars top down orientation', 'cue position or absence',
                'middle car position (shift)'])  # ... Results header


def main():
    global PART_ID  # PART_ID is used in case of error on @atexit, that's why it must be global

    # === Dialog popup ===
    info = {'IDENTYFIKATOR': '', u'P\u0141EC': ['M', "K"], 'WIEK': '20'}
    dictDlg = gui.DlgFromDict(
        dictionary=info, title='Experiment title, fill by your name!')
    if not dictDlg.OK:
        abort_with_error('Info dialog terminated.')

    clock = core.Clock()
    # load config, all params are there
    conf = yaml.full_load(open('config.yaml', encoding='utf-8'))

    # === Scene init ===
    win = visual.Window(list(SCREEN_RES.values()), fullscr=False, monitor='testMonitor', units='pix',
                        screen=0, color=conf['BACKGROUND_COLOR'])
    event.Mouse(visible=False, newPos=None, win=win)  # Make mouse invisible
    FRAME_RATE = get_frame_rate(win)

    # check if a detected frame rate is consistent with a frame rate for witch experiment was designed
    # important only if milisecond precision design is used
    if FRAME_RATE != conf['FRAME_RATE']:
        dlg = gui.Dlg(title="Critical error")
        dlg.addText(
            'Wrong no of frames detected: {}. Experiment terminated.'.format(FRAME_RATE))
        dlg.show()
        return None

    PART_ID = info['IDENTYFIKATOR'] + info[u'P\u0141EC'] + info['WIEK']
    logging.LogFile(join('results', PART_ID + '.log'),
                    level=logging.INFO)  # errors logging
    logging.info('FRAME RATE: {}'.format(FRAME_RATE))
    logging.info('SCREEN RES: {}'.format(SCREEN_RES.values()))

    # === Prepare stimulus here ===
    #
    # Examples:
    # fix_cross = visual.TextStim(win, text='+', height=100, color=conf['FIX_CROSS_COLOR'])
    # que = visual.Circle(win, radius=conf['QUE_RADIUS'], fillColor=conf['QUE_COLOR'], lineColor=conf['QUE_COLOR'])
    # stim = visual.TextStim(win, text='', height=conf['STIM_SIZE'], color=conf['STIM_COLOR'])
    # mask = visual.ImageStim(win, image='mask4.png', size=(conf['STIM_SIZE'], conf['STIM_SIZE']))
    background = visual.ImageStim(win, image='images/fixation.bmp')
    cue = visual.TextStim(win, text='*', height=2.0, color='black', units='deg', alignHoriz='center',
                          alignVert='center', alignText='center', anchorHoriz='center', anchorVert='center')
    car1 = visual.ImageStim(win, image='images/car.bmp', units='deg')
    car2 = visual.ImageStim(win, image='images/car.bmp', units='deg')
    car3 = visual.ImageStim(win, image='images/car.bmp', units='deg')
    car4 = visual.ImageStim(win, image='images/car.bmp', units='deg')
    car5 = visual.ImageStim(win, image='images/car.bmp', units='deg')

    trial_no = 0

    # === Training ===

    show_info(win, join('.', 'messages', 'ins1.txt'))
    show_info(win, join('.', 'messages', 'ins2.txt'))
    show_info(win, join('.', 'messages', 'ins3.txt'))
    show_info(win, join('.', 'messages', 'ins4.txt'))

    trial_no += 1

    for _ in range(conf['NO_TRAINING_TRIALS']):
        key_pressed, rt, cars_lr_orientation, middle_car_lr_orientation, \
        cars_td_orientation, cue_position, middle_car_position \
            = run_trial(win, conf, background, cue, car1, car2, car3, car4, car5, clock)
        if middle_car_position in ['left', 'right']:
            if key_pressed == 'space':
                corr = True
            else:
                corr = False
                cor_res = 'space'
        elif middle_car_lr_orientation == 'left':
            if key_pressed == 'c':
                corr = True
            else:
                corr = False
                cor_res = 'c'
        elif middle_car_lr_orientation == 'right':
            if key_pressed == 'm':
                corr = True
            else:
                corr = False
                cor_res = 'm'
        else:
            corr = False
        RESULTS.append([PART_ID, 'training', trial_no, key_pressed, rt, cars_lr_orientation,
                        middle_car_lr_orientation, cars_td_orientation, cue_position, middle_car_position])

        # it's often good presenting feedback in training trials
        feedb = 'Poprawnie!' if corr else f'Niepoprawnie...\nPoprawna to: [{cor_res}]'
        feedb = visual.TextStim(win, text=feedb, height=50, color='black')
        feedb.draw()
        win.flip()
        core.wait(1)
        win.flip()

        trial_no += 1

    # === Experiment ===

    show_info(win, join('.', 'messages', 'ins5.txt'))

    for block_no in range(conf['NO_BLOCKS']):
        for _ in range(conf['NO_TRIALS_IN_BLOCK']):
            key_pressed, rt, cars_lr_orientation, middle_car_lr_orientation, \
            cars_td_orientation, cue_position, middle_car_position \
                = run_trial(win, conf, background, cue, car1, car2, car3, car4, car5, clock)
            RESULTS.append([PART_ID, block_no, trial_no, key_pressed, rt, cars_lr_orientation,
                            middle_car_lr_orientation, cars_td_orientation, cue_position, middle_car_position])
            trial_no += 1

    # === Cleaning time ===

    save_beh_results()
    logging.flush()
    show_info(win, join('.', 'messages', 'ins6.txt'))
    win.close()
    core.quit()


def run_trial(win, conf, background, cue, car1, car2, car3, car4, car5, clock):
    """
    Prepare and present single trial of procedure.
    Input (params) should consist all data need for presenting stimuli.
    If some stimulus (eg. text, label, button) will be presented across many trials.
    Should be prepared outside this function and passed for .draw() or .setAutoDraw().

    All behavioral data (reaction time, answer, etc. should be returned from this function)
    """

    check_exit()

    # === Prepare trial-related stimulus ===

    cars_direction = random.choice([True, False])  # true means right, false means left
    middle_car_direction = random.choice([True, False])  # true means right, false means left
    middle_car_lr_orientation = 'right' if middle_car_direction else 'left'
    cars_lr_orientation = 'right' if cars_direction else 'left'
    car1.flipHoriz = cars_direction
    car2.flipHoriz = cars_direction
    car3.flipHoriz = middle_car_direction
    car4.flipHoriz = cars_direction
    car5.flipHoriz = cars_direction

    random_top_down = random.choice([-conf['STIM_VER_ANGLE'], conf['STIM_VER_ANGLE']])
    cars_td_orientation = 'top' if random_top_down == conf['STIM_VER_ANGLE'] else 'down'
    car1.pos = (-2 * conf['STIM_HOR_ANGLE'], random_top_down)
    car2.pos = (-1 * conf['STIM_HOR_ANGLE'], random_top_down)
    car4.pos = (+1 * conf['STIM_HOR_ANGLE'], random_top_down)
    car5.pos = (+2 * conf['STIM_HOR_ANGLE'], random_top_down)
    random_shift = random.random()
    if random_shift < conf['CAR_SHIFT_PROBABILITY']:
        if random_shift < conf['CAR_SHIFT_PROBABILITY'] / 2:
            middle_car_position = 'right'
            car3.pos = (+conf['STIM_HOR_ANGLE_SHIFT'], random_top_down)
        else:
            middle_car_position = 'left'
            car3.pos = (-conf['STIM_HOR_ANGLE_SHIFT'], random_top_down)
    else:
        middle_car_position = 'middle'
        car3.pos = (0.0, random_top_down)

    variable_time = random.randint(0, conf['VARIABLE_TIME'])
    random_cue = random.random()
    if random_cue < conf['INCORRECT_CUE_PROBABILITY']:
        cue_position = 'incorrect'
        cue.pos = (0.0, -random_top_down - 0.25)
    elif random_cue < conf['CUE_PROBABILITY']:
        cue_position = 'correct'
        cue.pos = (0.0, +random_top_down - 0.25)
    else:
        cue_position = 'none'

    # === Start pre-trial  stuff (Fixation cross etc.)===

    for _ in range(conf['PRE_STIM_TIME'] + variable_time):
        background.draw()
        win.flip()

    for _ in range(conf['CUE_TIME']):
        background.draw()
        if random_cue < conf['CUE_PROBABILITY']:
            cue.draw()
        win.flip()

    for _ in range(conf['CUE_TO_STIM_TIME']):
        background.draw()
        win.flip()

    # === Start trial ===
    # This part is time-crucial. All stims must be already prepared.
    # Only .draw() .flip() and reaction related stuff goes there.
    event.clearEvents()
    # make sure, that clock will be reset exactly when stimuli will be drawn
    win.callOnFlip(clock.reset)

    saved_reaction = None

    for _ in range(conf['STIM_TIME']):  # present stimuli
        if not saved_reaction:
            reaction = event.getKeys(keyList=list(conf['REACTION_KEYS']), timeStamped=clock)
            if reaction:
                saved_reaction = reaction
        background.draw()
        car1.draw()
        car2.draw()
        car3.draw()
        car4.draw()
        car5.draw()
        win.flip()

    for _ in range(conf['REACTION_TIME'] + conf['VARIABLE_TIME'] - variable_time):
        if not saved_reaction:
            reaction = event.getKeys(keyList=list(conf['REACTION_KEYS']), timeStamped=clock)
            if reaction:
                saved_reaction = reaction
        background.draw()
        win.flip()

    # === Trial ended, prepare data for send  ===
    if saved_reaction:
        key_pressed, rt = saved_reaction[0]
    else:  # timeout
        key_pressed = 'no_key'
        rt = -1.0

    return key_pressed, rt, cars_lr_orientation, middle_car_lr_orientation, \
           cars_td_orientation, cue_position, middle_car_position  # return all data collected during trial


if __name__ == '__main__':
    PART_ID = ''
    SCREEN_RES = get_screen_res()
    main()
