#!/usr/bin/env python3

import inkex, re, os, random, sys, subprocess, shutil
from inkex.command import inkscape

from outputpro import cmyk, cutmarks

from PyQt5 import QtGui, QtCore, uic, QtWidgets
from PyQt5.QtWidgets import QMainWindow, QApplication
from PyQt5.QtCore import *

import gettext
_ = gettext.gettext

import tempfile

dirpathTempFolder = tempfile.TemporaryDirectory(suffix=str(random.randint(0,9)), prefix="output-")
dirpathSoftware = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'outputpro')
uuconv = {
    "in": 96.0,
    "pt": 1.33333333333,
    "px": 1.0,
    "mm": 3.77952755913,
    "cm": 37.7952755913,
    "pc": 16.0}


def unittouu(string):
    '''Returns userunits given a string representation of units in another system'''
    unit = re.compile('(%s)$' % '|'.join(uuconv.keys()))
    param = re.compile(r'(([-+]?[0-9]+(\.[0-9]*)?|[-+]?\.[0-9]+)([eE][-+]?[0-9]+)?)')

    p = param.match(string)
    u = unit.search(string)
    if p:
        retval = float(p.string[p.start():p.end()])
    else:
        retval = 0.0
    if u:
        try:
            return retval * uuconv[u.string[u.start():u.end()]]
        except KeyError:
            pass
    return retval

class OutputPro(inkex.EffectExtension):
    
    def effect(self):
        if "nt" in os.name:
            icc_dir = 'C:\\Windows\\System32\\spool\\drivers\\color'
        else:
            icc_dir = '/usr/share/color/icc/colord/'
            #might be also ~/.local/share/icc/
            
        try:
            with open(os.path.join(os.path.abspath(inkex.utils.get_user_directory() + "/../"), "preferences.xml"), 'r') as f:
                inkscape_config = f.read()
            
            list_of_export_formats = ['JPEG']
            list_of_format_tips = {'JPEG':'The JPEG format always has some loss of quality. Although it supports CMYK, it is not recommended for use in printed graphics.'}
            list_of_color_modes_jpeg = ['CMYK','RGB','Gray','CMY','HSB','HSL','HWB','Lab','Log', 'OHTA','Rec601Luma','Rec601YCbCr','Rec709Luma','Rec709YCbCr','sRGB','XYZ','YCbCr','YCC','YIQ','YPbPr','YUV']
            list_of_interlacing_jpeg = {u'None':'none', u'Line':'line', u'Plane':'plane', u'Partition':'partition'}
            list_of_noise_jpeg = {u'Gaussian':'Gaussian-noise', u'Impulse':'Impulse-noise', u'Laplacian':'Laplacian-noise', u'Multiplicative':'Multiplicative-noise', u'Poisson':'Poisson-noise', u'Uniform':'Uniform-noise'}
            list_of_subsampling_jpeg = ['1x1, 1x1, 1x1', '2x1, 1x1, 1x1', '1x2, 1x1, 1x1', '2x2, 1x1, 1x1']
            list_of_dct_jpeg = {u'Integer':'int', u'Integer (fast)':'fast', u'Floating point':'float'}
            list_of_area_to_export = [_(u"Page"), _(u"Drawing"), _(u"Object")]#,  _(u"Área definida")]
            
            if "nt" in os.name:
                shell = True
            else:
                 shell = False

            selected_screen_profile = inkscape_config.split('id="displayprofile"')[1].split('uri="')[1].split('" />')[0].split('/')[-1]
            #if selected_screen_profile == '':
            #    inkex.utils.debug("Configured icc color profile (Inkscape) is not set. Configure it in preferences and restart Inkscape to apply changes.")
            selected_print_profile = inkscape_config.split('id="softproof"')[1].split('uri="')[1].split('" />')[0].split('/')[-1]
                    
            list_of_selected_objects = []
            for id, node in self.svg.selected.items():
                list_of_selected_objects.append(node.get('id'))
            if len(list_of_selected_objects) >= 1:
                selected_object = list_of_selected_objects[0]
            else:
                selected_object = 'layer1'
    
            resolution = '96'
    
            shutil.copy2(self.options.input_file, os.path.join(dirpathTempFolder.name, "original.svg")) # complete target filename given
    
            svg = self.document.getroot()
            page_width  = unittouu(svg.get('width'))
            page_height = unittouu(svg.get('height'))
    
            class mainWindow(QtWidgets.QWidget):
                    
                def __init__(self, parent=None):
                    QtWidgets.QWidget.__init__(self, parent)
                    self.resize(950, 600)
                    self.setMaximumSize(QtCore.QSize(950, 600))
                    self.setMinimumSize(QtCore.QSize(950, 600))
                    self.setWindowTitle(_(u'Inkscape Output Pro Bitmap'))
                    self.move(int((QtWidgets.QDesktopWidget().screenGeometry().width()-self.geometry().width())/2), int((QtWidgets.QDesktopWidget().screenGeometry().height()-self.geometry().height())/2))
    
                    self.preview_zoom = 1.0
    
                    self.top_title_bitmap = QtWidgets.QLabel(parent=self)
                    self.top_title_bitmap.setGeometry(0, 0, 950, 60)
                    self.top_title_bitmap.setPixmap(QtGui.QPixmap(os.path.join(dirpathSoftware, 'top.png')))
    
                    self.preview_panel = QtWidgets.QWidget(parent=self)
                    self.preview_panel.setGeometry(0, 0, 320, 600)
    
                    self.preview_bitmap = QtWidgets.QLabel(parent=self.preview_panel)
                    self.preview_bitmap.setGeometry(10, 70, 300, 300)
                    self.preview_bitmap.setPixmap(QtGui.QPixmap(os.path.join(dirpathTempFolder.name, 'preview.png')))
                    #self.preview_bitmap.setStyleSheet("QWidget { background: url(alpha.png)}")
                    #self.preview_bitmap.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignCenter)
    
                    self.preview_original_title = QtWidgets.QLabel(parent=self.preview_panel)
                    self.preview_original_title.setText(_(u"Original").upper())
                    self.preview_original_title.setGeometry(255, 355, 50, 10)
                    self.preview_original_title.setAlignment(QtCore.Qt.AlignCenter)
                    self.preview_original_title.setStyleSheet('QFrame{font:6pt;border-radius: 2px;padding: 2px;background-color:rgba(0,0,0,128);color:white}')
    
                    self.preview_result_title = QtWidgets.QLabel(parent=self.preview_panel)
                    self.preview_result_title.setText(_(u"Result").upper())
                    self.preview_result_title.setGeometry(15, 75, 50, 10)
                    self.preview_result_title.setAlignment(QtCore.Qt.AlignCenter)
                    self.preview_result_title.setStyleSheet('QFrame{font:6pt;border-radius: 2px;padding: 2px;background-color:rgba(0,0,0,128);color:white}')
    
                    self.zoom_out_button = QtWidgets.QPushButton(QtGui.QIcon.fromTheme("zoom-out"), '', parent=self.preview_panel)
                    self.zoom_out_button.setGeometry(10, 371, 16, 16)
                    self.zoom_out_button.setIconSize(QtCore.QSize(12,12))
                    self.zoom_out_button.setFlat(True)
                    self.zoom_out_button.clicked.connect(self.zoom_out)
    
                    self.zoom_in_button = QtWidgets.QPushButton(QtGui.QIcon.fromTheme("zoom-in"), '', parent=self.preview_panel)
                    self.zoom_in_button.setGeometry(26, 371, 16, 16)
                    self.zoom_in_button.setIconSize(QtCore.QSize(12,12))
                    self.zoom_in_button.setFlat(True)
                    self.zoom_in_button.clicked.connect(self.zoom_in)
    
                    self.preview_zoom_title = QtWidgets.QLabel(parent=self.preview_panel)
                    self.preview_zoom_title.setGeometry(44, 371, 256, 16)
                    self.preview_zoom_title.setText('100%')
                    self.preview_zoom_title.setAlignment(QtCore.Qt.AlignVCenter | QtCore.Qt.AlignLeft)
                    self.preview_zoom_title.setFont(QtGui.QFont('Ubuntu', 8))
                    #self.preview_result_title.setStyleSheet('QFrame{font:7pt;border-radius: 2px;padding: 2px;background-color:rgba(0,0,0,128);color:white}')
    
                    self.view_c_button = QtWidgets.QPushButton('C', parent=self.preview_panel)
                    self.view_c_button.setGeometry(246, 371, 16, 16)
                    self.view_c_button.setIconSize(QtCore.QSize(12,12))
                    self.view_c_button.setFlat(True)
                    self.view_c_button.setCheckable(True)
                    self.view_c_button.setChecked(True)
                    self.view_c_button.setVisible(False)
                    self.view_c_button.clicked.connect(self.cmyk_advanced_manipulation_view_separations)
    
                    self.view_m_button = QtWidgets.QPushButton('M', parent=self.preview_panel)
                    self.view_m_button.setGeometry(262, 371, 16, 16)
                    self.view_m_button.setIconSize(QtCore.QSize(12,12))
                    self.view_m_button.setFlat(True)
                    self.view_m_button.setCheckable(True)
                    self.view_m_button.setChecked(True)
                    self.view_m_button.setVisible(False)
                    self.view_m_button.clicked.connect(self.cmyk_advanced_manipulation_view_separations)
    
                    self.view_y_button = QtWidgets.QPushButton('Y', parent=self.preview_panel)
                    self.view_y_button.setGeometry(278, 371, 16, 16)
                    self.view_y_button.setIconSize(QtCore.QSize(12,12))
                    self.view_y_button.setFlat(True)
                    self.view_y_button.setCheckable(True)
                    self.view_y_button.setChecked(True)
                    self.view_y_button.setVisible(False)
                    self.view_y_button.clicked.connect(self.cmyk_advanced_manipulation_view_separations)
    
                    self.view_k_button = QtWidgets.QPushButton('K', parent=self.preview_panel)
                    self.view_k_button.setGeometry(294, 371, 16, 16)
                    self.view_k_button.setIconSize(QtCore.QSize(12,12))
                    self.view_k_button.setFlat(True)
                    self.view_k_button.setCheckable(True)
                    self.view_k_button.setChecked(True)
                    self.view_k_button.setVisible(False)
                    self.view_k_button.clicked.connect(self.cmyk_advanced_manipulation_view_separations)
    
                    self.view_image_info = QtWidgets.QLabel(parent=self.preview_panel)
                    self.view_image_info.setGeometry(10, 400, 300, 190)
                    self.view_image_info.setFont(QtGui.QFont('Ubuntu', 8))
                    self.view_image_info.setWordWrap(True)
                    self.view_image_info.setAlignment(QtCore.Qt.AlignTop)
    
                    self.format_title = QtWidgets.QLabel(parent=self)
                    self.format_title.setText(_(u"Format").upper())
                    self.format_title.setGeometry(320, 70, 200, 15)
                    self.format_title.setFont(QtGui.QFont('Ubuntu', 8, 75))
    
                    self.format_choice = QtWidgets.QComboBox(parent=self)
                    self.format_choice.setGeometry(320, 85, 200, 25)
                    self.format_choice.addItems(list_of_export_formats)
                    self.format_choice.activated.connect(self.change_format)
    
                    self.format_preview_check = QtWidgets.QCheckBox(parent=self)
                    self.format_preview_check.setGeometry(540, 85, 200, 25)
                    self.format_preview_check.setText(_(u"Preview"))
                    self.format_preview_check.setChecked(True)
                    self.format_preview_check.clicked.connect(self.format_preview_change)
    
                    self.option_box = QtWidgets.QTabWidget(parent=self)
                    self.option_box.setGeometry(320, 120, 620, 435)
    
                    self.general_options_panel = QtWidgets.QWidget(parent=self)
                    self.general_geometry_panel = QtWidgets.QWidget(parent=self)
                    self.general_prepress_panel = QtWidgets.QWidget(parent=self)
                    self.general_imposition_panel = QtWidgets.QWidget(parent=self)
                    self.option_box.addTab(self.general_options_panel, _(u"Options"))
                    self.option_box.addTab(self.general_geometry_panel, _(u"Size"))
                    self.option_box.addTab(self.general_prepress_panel, _(u"Prepress"))
                    self.option_box.addTab(self.general_imposition_panel, _(u"Imposition"))
    
                    self.option_box.currentChanged.connect(self.generate_preview)
    
                    self.general_options_panel_jpeg = QtWidgets.QWidget(parent=self.general_options_panel)
                    self.general_options_panel_jpeg.setVisible(False)
    
                    self.icc_dir_textbox_label = QtWidgets.QLabel(parent=self.general_options_panel_jpeg)
                    self.icc_dir_textbox_label.setText(_(u"ICC profile folder"))
                    self.icc_dir_textbox_label.setGeometry(10, 280, 120, 25)
    
                    self.icc_dir_textbox = QtWidgets.QLineEdit(parent=self.general_options_panel_jpeg)
                    self.icc_dir_textbox.setReadOnly(True)
                    self.icc_dir_textbox.setGeometry(130, 280, 260, 25)
                    self.icc_dir_textbox.setText(icc_dir)

                    self.icc_dir_button = QtWidgets.QPushButton(_("Change"), parent=self.general_options_panel_jpeg)
                    self.icc_dir_button.setGeometry(403, 280, 70, 25)
                    self.icc_dir_button.clicked.connect(self.change_icc_dir)

                    self.color_mode_title_jpeg = QtWidgets.QLabel(parent=self.general_options_panel_jpeg)
                    self.color_mode_title_jpeg.setText(_(u"Color mode").upper())
                    self.color_mode_title_jpeg.setGeometry(10, 10, 260, 15)
                    self.color_mode_title_jpeg.setFont(QtGui.QFont('Ubuntu', 8))
    
                    self.color_mode_choice_jpeg = QtWidgets.QComboBox(parent=self.general_options_panel_jpeg)
                    self.color_mode_choice_jpeg.setGeometry(10, 25, 260, 25)
                    self.color_mode_choice_jpeg.addItems(list_of_color_modes_jpeg)
                    self.color_mode_choice_jpeg.activated.connect(self.change_color_mode_jpeg)
    
                    self.color_mode_title_tip_jpeg = QtWidgets.QLabel(parent=self.general_options_panel_jpeg)
                    self.color_mode_title_tip_jpeg.setGeometry(10, 50, 260, 15)
                    self.color_mode_title_tip_jpeg.setFont(QtGui.QFont('Ubuntu', 7))
    
                    self.quality_title_jpeg = QtWidgets.QLabel(parent=self.general_options_panel_jpeg)
                    self.quality_title_jpeg.setText(_(u"Quality").upper())
                    self.quality_title_jpeg.setGeometry(285, 10, 100, 15)
                    self.quality_title_jpeg.setFont(QtGui.QFont('Ubuntu', 8))
    
                    jpeg_quality = 100
                    self.quality_percent_title_jpeg = QtWidgets.QLabel(parent=self.general_options_panel_jpeg)
                    self.quality_percent_title_jpeg.setText('{}%'.format(jpeg_quality))
                    self.quality_percent_title_jpeg.setGeometry(505, 10, 100, 40)
                    self.quality_percent_title_jpeg.setFont(QtGui.QFont('Ubuntu', 12, 75))
                    self.quality_percent_title_jpeg.setAlignment(QtCore.Qt.AlignRight)
    
                    self.quality_percent_title_left_jpeg = QtWidgets.QLabel(parent=self.general_options_panel_jpeg)
                    self.quality_percent_title_left_jpeg.setText('Lower quality\nSmaller file')
                    self.quality_percent_title_left_jpeg.setGeometry(285, 40, 160, 35)
                    self.quality_percent_title_left_jpeg.setFont(QtGui.QFont('Ubuntu', 7))
                    self.quality_percent_title_left_jpeg.setAlignment(QtCore.Qt.AlignLeft)
    
                    self.quality_percent_title_right_jpeg = QtWidgets.QLabel(parent=self.general_options_panel_jpeg)
                    self.quality_percent_title_right_jpeg.setText('Higher quality<br>Larger file')
                    self.quality_percent_title_right_jpeg.setGeometry(445, 40, 160, 35)
                    self.quality_percent_title_right_jpeg.setFont(QtGui.QFont('Ubuntu', 7))
                    self.quality_percent_title_right_jpeg.setAlignment(QtCore.Qt.AlignRight)
    
                    self.quality_choice_dial_jpeg = QtWidgets.QDial(parent=self.general_options_panel_jpeg)
                    self.quality_choice_dial_jpeg.setRange(1,100)
                    self.quality_choice_dial_jpeg.setGeometry(415, 10, 60, 60)
                    self.quality_choice_dial_jpeg.setNotchesVisible(True)
                    self.quality_choice_dial_jpeg.setValue(jpeg_quality)
                    self.quality_choice_dial_jpeg.sliderReleased.connect(self.generate_preview)
                    self.quality_choice_dial_jpeg.valueChanged.connect(self.change_quality_live_jpeg)
    
                    self.color_profile_choice_jpeg = QtWidgets.QCheckBox(_(u"Use Inkscape color profile"), parent=self.general_options_panel_jpeg)
                    self.color_profile_choice_jpeg.setChecked(False)
                    self.color_profile_choice_jpeg.setGeometry(283, 150, 325, 25)
                    self.color_profile_choice_jpeg.clicked.connect(self.generate_preview)
    
                    self.document_color_profile_title_jpeg = QtWidgets.QLabel(parent=self.general_options_panel_jpeg)
                    self.document_color_profile_title_jpeg.setGeometry(290, 175, 320, 30)
                    self.document_color_profile_title_jpeg.setWordWrap(True)
                    self.document_color_profile_title_jpeg.setFont(QtGui.QFont('Ubuntu', 7))
                    self.document_color_profile_title_jpeg.setAlignment(QtCore.Qt.AlignLeft)
    
                    if selected_print_profile == '':
                        self.document_color_profile_title_jpeg.setEnabled(False)
                        self.color_profile_choice_jpeg.setEnabled(False)
                        self.document_color_profile_title_jpeg.setText(_(u"This document is not using a color profile."))
                    else:
                        self.document_color_profile_title_jpeg.setText(_(u"The profile used by Inkscape is") + ' ' + selected_print_profile[:-4])
    
                    self.jpeg_interlace_option_jpeg = QtWidgets.QCheckBox(_(u"Interlace"), parent=self.general_options_panel_jpeg)
                    self.jpeg_interlace_option_jpeg.setGeometry(10, 80, 120, 25)
                    self.jpeg_interlace_option_jpeg.toggled.connect(self.jpeg_interlace_click_jpeg)
    
                    self.jpeg_interlace_choice_jpeg = QtWidgets.QComboBox(parent=self.general_options_panel_jpeg)
                    self.jpeg_interlace_choice_jpeg.setGeometry(130, 80, 140, 25)
                    self.jpeg_interlace_choice_jpeg.addItems(list_of_interlacing_jpeg.keys())
                    self.jpeg_interlace_choice_jpeg.setCurrentIndex(1)
                    self.jpeg_interlace_choice_jpeg.setEnabled(False)
                    self.jpeg_interlace_choice_jpeg.activated.connect(self.generate_preview)
    
                    self.jpeg_optimize_option_jpeg = QtWidgets.QCheckBox(_(u"Optimize"), parent=self.general_options_panel_jpeg)
                    self.jpeg_optimize_option_jpeg.setGeometry(10, 115, 260, 25)
                    self.jpeg_optimize_option_jpeg.setChecked(True)
    
                    self.jpeg_noise_option_jpeg = QtWidgets.QCheckBox(_(u"Noise"), parent=self.general_options_panel_jpeg)
                    self.jpeg_noise_option_jpeg.setGeometry(10, 150, 120, 25)
                    self.jpeg_noise_option_jpeg.toggled.connect(self.jpeg_noise_click_jpeg)
    
                    self.jpeg_noise_choice_jpeg = QtWidgets.QComboBox(parent=self.general_options_panel_jpeg)
                    self.jpeg_noise_choice_jpeg.setGeometry(130, 150, 140, 25)
                    self.jpeg_noise_choice_jpeg.addItems(list_of_noise_jpeg.keys())
                    self.jpeg_noise_choice_jpeg.setCurrentIndex(1)
                    self.jpeg_noise_choice_jpeg.setEnabled(False)
                    self.jpeg_noise_choice_jpeg.activated.connect(self.generate_preview)
    
                    self.jpeg_noise_ammount_jpeg = QtWidgets.QSlider(QtCore.Qt.Horizontal, parent=self.general_options_panel_jpeg)
                    self.jpeg_noise_ammount_jpeg.setGeometry(10, 170, 260, 25)
                    self.jpeg_noise_ammount_jpeg.setRange(0,100)
                    self.jpeg_noise_ammount_jpeg.setEnabled(False)
                    self.jpeg_noise_ammount_jpeg.setValue(0)
                    self.jpeg_noise_ammount_jpeg.sliderReleased.connect(self.generate_preview)
    
                    self.jpeg_subsampling_option_jpeg = QtWidgets.QLabel(parent=self.general_options_panel_jpeg)
                    self.jpeg_subsampling_option_jpeg.setText(_(u"Sub-sampling"))
                    self.jpeg_subsampling_option_jpeg.setGeometry(10, 210, 140, 25)
    
                    self.jpeg_subsampling_choice_jpeg = QtWidgets.QComboBox(parent=self.general_options_panel_jpeg)
                    self.jpeg_subsampling_choice_jpeg.setGeometry(150, 210, 120, 25)
                    self.jpeg_subsampling_choice_jpeg.addItems(list_of_subsampling_jpeg)
                    self.jpeg_subsampling_choice_jpeg.setCurrentIndex(0)
                    self.jpeg_subsampling_choice_jpeg.activated.connect(self.generate_preview)
    
                    self.jpeg_dct_option_jpeg = QtWidgets.QLabel(parent=self.general_options_panel_jpeg)
                    self.jpeg_dct_option_jpeg.setText(_(u"DCT Method"))
                    self.jpeg_dct_option_jpeg.setGeometry(10, 245, 120, 25)
    
                    self.jpeg_dct_choice_jpeg = QtWidgets.QComboBox(parent=self.general_options_panel_jpeg)
                    self.jpeg_dct_choice_jpeg.setGeometry(130, 245, 140, 25)
                    self.jpeg_dct_choice_jpeg.addItems(list_of_dct_jpeg.keys())
                    self.jpeg_dct_choice_jpeg.activated.connect(self.generate_preview)
    
                    self.cmyk_advanced_manipulation_option_jpeg = QtWidgets.QCheckBox(_(u"Accurate color handling"), parent=self.general_options_panel_jpeg)
                    self.cmyk_advanced_manipulation_option_jpeg.setGeometry(283, 80, 325, 25)
                    self.cmyk_advanced_manipulation_option_jpeg.clicked.connect(self.cmyk_advanced_manipulation_click_jpeg)
    
                    self.cmyk_overblack_jpeg = QtWidgets.QCheckBox(_(u"Black overlay"), parent=self.general_options_panel_jpeg)
                    self.cmyk_overblack_jpeg.setGeometry(283, 115, 325, 25)
                    self.cmyk_overblack_jpeg.setEnabled(False)
                    self.cmyk_overblack_jpeg.clicked.connect(self.cmyk_advanced_manipulation_click_jpeg)
    
                    self.area_to_export_title = QtWidgets.QLabel(parent=self.general_geometry_panel)
                    self.area_to_export_title.setText(_(u"Area to export").upper())
                    self.area_to_export_title.setGeometry(10, 20, 250, 15)
                    self.area_to_export_title.setFont(QtGui.QFont('Ubuntu', 8))
    
                    self.area_to_export_choice = QtWidgets.QComboBox(parent=self.general_geometry_panel)
                    self.area_to_export_choice.setGeometry(10, 35, 250, 25)
                    self.area_to_export_choice.addItems(list_of_area_to_export)
                    self.area_to_export_choice.activated.connect(self.change_area_to_export)
    
                    self.dpi_title = QtWidgets.QLabel(parent=self.general_geometry_panel)
                    self.dpi_title.setText(_(u"Dots per inch").upper())
                    self.dpi_title.setGeometry(270, 20, 200, 15)
                    self.dpi_title.setFont(QtGui.QFont('Ubuntu', 8))
    
                    self.dpi_choice = QtWidgets.QSpinBox(parent=self.general_geometry_panel)
                    self.dpi_choice.setValue(96)
                    self.dpi_choice.setGeometry(270, 35, 100, 25)
                    self.dpi_choice.setRange(1, 99999)
                    self.dpi_choice.editingFinished.connect(self.change_area_to_export)
    
                    self.dpi_text_title = QtWidgets.QLabel(parent=self.general_geometry_panel)
                    self.dpi_text_title.setText('dpi')
                    self.dpi_text_title.setGeometry(380, 35, 80, 25)
                    self.dpi_text_title.setFont(QtGui.QFont('Ubuntu', 8))
    
                    self.x0_value = QtWidgets.QSpinBox(parent=self.general_geometry_panel)
                    self.x0_value.setGeometry(10, 100, 80, 25)
                    self.x0_value.setRange(1, 2147483647)
                    self.x0_value.editingFinished.connect(self.change_area_to_export)
    
                    self.y0_value = QtWidgets.QSpinBox(parent=self.general_geometry_panel)
                    self.y0_value.setGeometry(100, 130, 80, 25)
                    self.y0_value.setRange(1, 2147483647)
                    self.y0_value.editingFinished.connect(self.change_area_to_export)
    
                    self.x1_value = QtWidgets.QSpinBox(parent=self.general_geometry_panel)
                    self.x1_value.setGeometry(100, 70, 80, 25)
                    self.x1_value.setRange(1, 2147483647)
                    self.x1_value.editingFinished.connect(self.change_area_to_export)
    
                    self.y1_value = QtWidgets.QSpinBox(parent=self.general_geometry_panel)
                    self.y1_value.setGeometry(190, 100, 80, 25)
                    self.y1_value.setRange(1, 2147483647)
                    self.y1_value.editingFinished.connect(self.change_area_to_export)
    
                    self.area_to_export_id_title = QtWidgets.QLabel(parent=self.general_geometry_panel)
                    self.area_to_export_id_title.setText(_(u"Object to be exported").upper())
                    self.area_to_export_id_title.setGeometry(10, 70, 300, 15)
                    self.area_to_export_id_title.setFont(QtGui.QFont('Ubuntu', 8))
    
                    self.area_to_export_id_name = QtWidgets.QLineEdit(parent=self.general_geometry_panel)
                    self.area_to_export_id_name.setGeometry(10, 85, 300, 25)
    
                    self.area_to_export_idonly_check = QtWidgets.QCheckBox(parent=self.general_geometry_panel)
                    self.area_to_export_idonly_check.setGeometry(10, 120, 400, 25)
                    self.area_to_export_idonly_check.setText(_(u"Export only object"))
    
                    self.prepress_paper_settings_label = QtWidgets.QLabel(parent=self.general_prepress_panel)
                    self.prepress_paper_settings_label.setGeometry(10, 10, 300, 15)
                    self.prepress_paper_settings_label.setText(_(u"Paper or film setting").upper())
                    self.prepress_paper_settings_label.setFont(QtGui.QFont('Ubuntu', 8))
    
                    self.prepress_paper_settings_invert = QtWidgets.QCheckBox(parent=self.general_prepress_panel)
                    self.prepress_paper_settings_invert.setGeometry(10, 25, 300, 25)
                    self.prepress_paper_settings_invert.setText(_(u"Invert"))
                    self.prepress_paper_settings_invert.setChecked(False)
                    self.prepress_paper_settings_invert.clicked.connect(self.generate_preview)
    
                    self.prepress_paper_settings_mirror = QtWidgets.QCheckBox(parent=self.general_prepress_panel)
                    self.prepress_paper_settings_mirror.setGeometry(10, 50, 300, 25)
                    self.prepress_paper_settings_mirror.setText(_(u"Mirror"))
                    self.prepress_paper_settings_mirror.setChecked(False)
                    self.prepress_paper_settings_mirror.clicked.connect(self.generate_preview)
    
                    self.prepress_paper_cutmarks_label = QtWidgets.QLabel(parent=self.general_prepress_panel)
                    self.prepress_paper_cutmarks_label.setGeometry(10, 85, 300, 15)
                    self.prepress_paper_cutmarks_label.setText(_(u"Crop marks").upper())
                    self.prepress_paper_cutmarks_label.setFont(QtGui.QFont('Ubuntu', 8))
    
                    self.prepress_paper_cutmarks_check = QtWidgets.QCheckBox(parent=self.general_prepress_panel)
                    self.prepress_paper_cutmarks_check.setGeometry(10, 100, 300, 25)
                    self.prepress_paper_cutmarks_check.setText(_(u"Insert crop marks"))
                    self.prepress_paper_cutmarks_check.setChecked(False)
                    self.prepress_paper_cutmarks_check.clicked.connect(self.cut_marks_insert_change)
    
                    self.prepress_paper_cutmarks_strokewidth_label = QtWidgets.QLabel(parent=self.general_prepress_panel)
                    self.prepress_paper_cutmarks_strokewidth_label.setGeometry(10, 125, 200, 25)
                    self.prepress_paper_cutmarks_strokewidth_label.setText(_(u"Mark thickness:"))
                    self.prepress_paper_cutmarks_strokewidth_label.setEnabled(False)
    
                    self.prepress_paper_cutmarks_strokewidth_value = QtWidgets.QLineEdit(parent=self.general_prepress_panel)
                    self.prepress_paper_cutmarks_strokewidth_value.setGeometry(210, 125, 50, 25)
                    self.prepress_paper_cutmarks_strokewidth_value.setText('1')
                    self.prepress_paper_cutmarks_strokewidth_value.setEnabled(False)
                    self.prepress_paper_cutmarks_strokewidth_value.editingFinished.connect(self.generate_preview)
    
                    self.prepress_paper_cutmarks_strokewidth_choice = QtWidgets.QComboBox(parent=self.general_prepress_panel)
                    self.prepress_paper_cutmarks_strokewidth_choice.setGeometry(260,125,50,25)
                    self.prepress_paper_cutmarks_strokewidth_choice.addItems(uuconv.keys())
                    self.prepress_paper_cutmarks_strokewidth_choice.setCurrentIndex(5)
                    self.prepress_paper_cutmarks_strokewidth_choice.activated.connect(self.generate_preview)
                    self.prepress_paper_cutmarks_strokewidth_choice.setEnabled(False)
    
                    self.prepress_paper_cutmarks_bleedsize_label = QtWidgets.QLabel(parent=self.general_prepress_panel)
                    self.prepress_paper_cutmarks_bleedsize_label.setGeometry(10, 150, 200, 25)
                    self.prepress_paper_cutmarks_bleedsize_label.setText(_(u"Bleed:"))
                    self.prepress_paper_cutmarks_bleedsize_label.setEnabled(False)
    
                    self.prepress_paper_cutmarks_bleedsize_value = QtWidgets.QLineEdit(parent=self.general_prepress_panel)
                    self.prepress_paper_cutmarks_bleedsize_value.setGeometry(210, 150, 50, 25)
                    self.prepress_paper_cutmarks_bleedsize_value.setText('5')
                    self.prepress_paper_cutmarks_bleedsize_value.setEnabled(False)
                    self.prepress_paper_cutmarks_bleedsize_value.editingFinished.connect(self.generate_preview)
    
                    self.prepress_paper_cutmarks_bleedsize_choice = QtWidgets.QComboBox(parent=self.general_prepress_panel)
                    self.prepress_paper_cutmarks_bleedsize_choice.setGeometry(260,150,50,25)
                    self.prepress_paper_cutmarks_bleedsize_choice.addItems(uuconv.keys())
                    self.prepress_paper_cutmarks_bleedsize_choice.setCurrentIndex(5)
                    self.prepress_paper_cutmarks_bleedsize_choice.activated.connect(self.generate_preview)
                    self.prepress_paper_cutmarks_bleedsize_choice.setEnabled(False)
    
                    self.prepress_paper_cutmarks_marksize_label = QtWidgets.QLabel(parent=self.general_prepress_panel)
                    self.prepress_paper_cutmarks_marksize_label.setGeometry(10, 175, 200, 25)
                    self.prepress_paper_cutmarks_marksize_label.setText(_(u"Mark size:"))
                    self.prepress_paper_cutmarks_marksize_label.setEnabled(False)
    
                    self.prepress_paper_cutmarks_marksize_value = QtWidgets.QLineEdit(parent=self.general_prepress_panel)
                    self.prepress_paper_cutmarks_marksize_value.setGeometry(210, 175, 50, 25)
                    self.prepress_paper_cutmarks_marksize_value.setText('5')
                    self.prepress_paper_cutmarks_marksize_value.setEnabled(False)
                    self.prepress_paper_cutmarks_marksize_value.editingFinished.connect(self.generate_preview)
    
                    self.prepress_paper_cutmarks_marksize_choice = QtWidgets.QComboBox(parent=self.general_prepress_panel)
                    self.prepress_paper_cutmarks_marksize_choice.setGeometry(260,175,50,25)
                    self.prepress_paper_cutmarks_marksize_choice.addItems(uuconv.keys())
                    self.prepress_paper_cutmarks_marksize_choice.setCurrentIndex(5)
                    self.prepress_paper_cutmarks_marksize_choice.activated.connect(self.generate_preview)
                    self.prepress_paper_cutmarks_marksize_choice.setEnabled(False)
    
                    self.prepress_paper_cutmarks_inside_check = QtWidgets.QCheckBox(parent=self.general_prepress_panel)
                    self.prepress_paper_cutmarks_inside_check.setGeometry(10, 200, 300, 25)
                    self.prepress_paper_cutmarks_inside_check.setText(_(u"No internal marks"))
                    self.prepress_paper_cutmarks_inside_check.setChecked(False)
                    self.prepress_paper_cutmarks_inside_check.setEnabled(False)
                    self.prepress_paper_cutmarks_inside_check.clicked.connect(self.generate_preview)
    
                    self.imposition_label = QtWidgets.QLabel(parent=self.general_imposition_panel)
                    self.imposition_label.setGeometry(10, 10, 300, 15)
                    self.imposition_label.setText(_(u"Amount of impositions").upper())
                    self.imposition_label.setFont(QtGui.QFont('Ubuntu', 8))
    
                    self.imposition_vertical_number_label = QtWidgets.QLabel(parent=self.general_imposition_panel)
                    self.imposition_vertical_number_label.setGeometry(10, 25, 200, 25)
                    self.imposition_vertical_number_label.setText(_(u"Lines:"))
    
                    self.imposition_vertical_number_value = QtWidgets.QSpinBox(parent=self.general_imposition_panel)
                    self.imposition_vertical_number_value.setGeometry(210, 25, 50, 25)
                    self.imposition_vertical_number_value.setValue(1)
                    self.imposition_vertical_number_value.setRange(1, 999)
                    self.imposition_vertical_number_value.editingFinished.connect(self.generate_preview)
    
                    self.imposition_horizontal_number_label = QtWidgets.QLabel(parent=self.general_imposition_panel)
                    self.imposition_horizontal_number_label.setGeometry(10, 60, 200, 25)
                    self.imposition_horizontal_number_label.setText(_(u"Columns:"))
    
                    self.imposition_horizontal_number_value = QtWidgets.QSpinBox(parent=self.general_imposition_panel)
                    self.imposition_horizontal_number_value.setGeometry(210, 60, 50, 25)
                    self.imposition_horizontal_number_value.setValue(1)
                    self.imposition_horizontal_number_value.setRange(1, 999)
                    self.imposition_horizontal_number_value.editingFinished.connect(self.generate_preview)
    
                    self.imposition_space_label = QtWidgets.QLabel(parent=self.general_imposition_panel)
                    self.imposition_space_label.setGeometry(10, 90, 200, 25)
                    self.imposition_space_label.setText(_(u"Space between marks:"))
    
                    self.imposition_space_value = QtWidgets.QLineEdit(parent=self.general_imposition_panel)
                    self.imposition_space_value.setGeometry(210, 90, 50, 25)
                    self.imposition_space_value.setText('5')
                    self.imposition_space_value.editingFinished.connect(self.generate_preview)
    
                    self.imposition_space_choice = QtWidgets.QComboBox(parent=self.general_imposition_panel)
                    self.imposition_space_choice.setGeometry(260,90,50,25)
                    self.imposition_space_choice.addItems(uuconv.keys())
                    self.imposition_space_choice.setCurrentIndex(5)
                    self.imposition_space_choice.activated.connect(self.generate_preview)
    
                    self.export_button = QtWidgets.QPushButton(QtGui.QIcon.fromTheme("document-export"), _("Export"), parent=self)
                    self.export_button.setGeometry(740, 560, 200, 30)
                    self.export_button.setIconSize(QtCore.QSize(20,20))
                    self.export_button.clicked.connect(self.export)
    
                    self.change_area_to_export()
                    self.change_format()
    
                def generate_preview(self):
                    if self.format_preview_check.isChecked():
                        self.generate_final_file()
    
                        if self.option_box.currentIndex() == 0:
                            self.preview_original_title.setVisible(True)
                            self.preview_result_title.setVisible(True)
    
                            final_command = ['convert']
                            final_command.append(os.path.join(dirpathTempFolder.name, 'result-imp.') + list_of_export_formats[self.format_choice.currentIndex()].lower())
    
                            if self.color_profile_choice_jpeg.isChecked():
                                final_command.append('-profile')
                                final_command.append(os.path.join(self.icc_dir_textbox.text(), selected_screen_profile))
    
                            final_command.append(os.path.join(dirpathTempFolder.name, 'result.png'))
                            subprocess.Popen(final_command, shell=shell).wait()
    
                            file_info = subprocess.Popen(['identify', os.path.join(dirpathTempFolder.name,  'source.png')], shell=shell, stdout=subprocess.PIPE).communicate()[0].decode('UTF-8')
                            image_width = int(file_info.split(' ')[2].split('x')[0])
                            image_height = int(file_info.split(' ')[2].split('x')[1])
    
                            marksize = (self.dpi_choice.value() / 96) * unittouu(str(self.prepress_paper_cutmarks_marksize_value.text()) + str(self.prepress_paper_cutmarks_marksize_choice.currentText()))
                            imposition_space = (self.dpi_choice.value() / 96) * unittouu(str(self.imposition_space_value.text()) + str(self.imposition_space_choice.currentText()))
    
                            file_info = subprocess.Popen(['identify', '-verbose', os.path.join(dirpathTempFolder.name,  'result-imp.') + list_of_export_formats[self.format_choice.currentIndex()].lower()], shell=shell, stdout=subprocess.PIPE).communicate()[0].decode('UTF-8')
                            file_info_final = ''
                            for line in file_info.split('\n'):
                                if '  Format: ' in line:
                                    file_info_final += 'Image Format: <strong>' + line.replace('  Format: ', '') + '</strong><br>'
                                if '  Geometry: ' in line:
                                    file_info_final += 'Width and height: <strong>' + line.replace('  Geometry: ', '').split('+')[0] + '</strong><br>'
                                if '  Resolution: ' in line:
                                    file_info_final += 'Resolution: <strong>' + line.replace('  Resolution: ', '')
                                if '  Units: ' in line:
                                    file_info_final += ' ' + line.replace('  Units: ', '').replace('Per', ' per ').replace('Pixels', 'pixels').replace('Centimeter', 'centimeter').replace('Inch', 'inch') + '</strong><br>'
                                if '  Colorspace: ' in line:
                                    file_info_final += 'Colorspace: <strong>' + line.replace('  Colorspace: ', '') + '</strong><br>'
                                if '  Depth: ' in line:
                                    file_info_final += 'Depth: <strong>' + line.replace('  Depth: ', '') + '</strong><br>'
                                if '  Quality: ' in line:
                                    file_info_final += 'Quality: <strong>' + line.replace('  Quality: ', '') + '%</strong><br>'
                                if '  Filesize: ' in line:
                                    file_info_final += 'Filesize: <strong>' + line.replace('  Filesize: ', '') + '</strong><br>'
                                if '    jpeg:sampling-factor: ' in line:
                                    file_info_final += 'Sampling: <strong>' + line.replace('    jpeg:sampling-factor: ', '') + '</strong><br>'
    
                            if self.prepress_paper_cutmarks_check.isChecked():
                                margin = marksize
                            else:
                                margin = imposition_space
    
                            if image_width < 300 or image_height < 300:
                                what_show = '-extent ' + str(int(300 * self.preview_zoom)) + 'x' + str(int(300 * self.preview_zoom)) + '-' + str(int(150 * self.preview_zoom) - int(image_width / 2)) + '-' + str(int(150 * self.preview_zoom) - int(image_height / 2))
                            else:
                                what_show = '-crop ' + str(int(300 * self.preview_zoom)) + 'x' + str(int(300 * self.preview_zoom)) + '+' + str(int(image_width / 2) - int(150 * self.preview_zoom)) + '+' + str(int(image_height / 2) - int(150 * self.preview_zoom))
                            os.system('convert "' + os.path.join(dirpathTempFolder.name,  'source.png') +  '" ' + what_show + ' "' + os.path.join(dirpathTempFolder.name,  'original.png') +  '"' )
    
                            if image_width < 300 or image_height < 300:
                                what_show = '-extent ' + str(int(300 * self.preview_zoom)) + 'x' + str(int(300 * self.preview_zoom)) + '-' + str(int(150 * self.preview_zoom) - int(image_width / 2) - margin) + '-' + str(int(150 * self.preview_zoom) - int(image_height / 2) - margin)
                            else:
                                what_show = '-crop ' + str(int(300 * self.preview_zoom)) + 'x' + str(int(300 * self.preview_zoom)) + '+' + str(int(image_width / 2) - int(150 * self.preview_zoom) + margin) + '+' + str(int(image_height / 2) - int(150 * self.preview_zoom) + margin)
    
                            os.system('convert "' + os.path.join(dirpathTempFolder.name,  'result.png') +  '" ' + what_show + ' "' + os.path.join(dirpathTempFolder.name,  'result.png') +  '"' )
    
                            if not self.preview_zoom == 1:
                                os.system('convert "' + os.path.join(dirpathTempFolder.name,  'original.png') +  '" -filter box -resize 300x300 "' + os.path.join(dirpathTempFolder.name,  'original.png') +  '"' )
                                os.system('convert "' + os.path.join(dirpathTempFolder.name,  'result.png') +  '" -filter box -resize 300x300 "' + os.path.join(dirpathTempFolder.name,  'result.png') +  '"' )
    
                            os.system(
                                'convert "' + 
                                os.path.join(dirpathTempFolder.name, 'original.png') +  
                                '" "' + 
                                os.path.join(dirpathTempFolder.name, 'result.png') +  
                                '" "' + 
                                os.path.join(dirpathSoftware, 'preview_mask.png') + #static file from extension directory
                                '" -composite "' +  
                                os.path.join(dirpathTempFolder.name, 'preview.png') +  
                                '"'
                                )
    
                            self.view_image_info.setText(file_info_final + '<br><small>' + list_of_format_tips[list_of_export_formats[self.format_choice.currentIndex()]] + '</small>')
    
                        elif self.option_box.currentIndex() == 1:
                            self.preview_original_title.setVisible(False)
                            self.preview_result_title.setVisible(False)
    
                            subprocess.Popen(['convert', os.path.join(dirpathTempFolder.name,  'result-imp.') + list_of_export_formats[self.format_choice.currentIndex()].lower(), '-resize', '300x300', os.path.join(dirpathTempFolder.name, 'preview.png')], shell=shell).wait()
    
                        elif self.option_box.currentIndex() == 2:
                            None
    
                        elif self.option_box.currentIndex() == 3:
                            None
    
                        self.preview_bitmap.setPixmap(QtGui.QPixmap(os.path.join(dirpathTempFolder.name, 'preview.png')))
    
                def generate_final_file(self):
                    if list_of_export_formats[self.format_choice.currentIndex()] == 'JPEG':
                        jpeg_command = ['convert']
    
                        if not self.cmyk_advanced_manipulation_option_jpeg.isChecked():
                            pre_command = ['convert']
                            pre_command.append(os.path.join(dirpathTempFolder.name, 'source.tiff'))
    
                            if list_of_color_modes_jpeg[self.color_mode_choice_jpeg.currentIndex()] == 'CMYK' or list_of_color_modes_jpeg[self.color_mode_choice_jpeg.currentIndex()] == 'RGB':
                                if self.color_profile_choice_jpeg.isChecked():
                                    pre_command.append('-profile')
                                    pre_command.append(os.path.join(self.icc_dir_textbox.text(), selected_screen_profile))
    
                                if list_of_color_modes_jpeg[self.color_mode_choice_jpeg.currentIndex()] == 'RGB':
                                    pre_command.append(os.path.join(dirpathTempFolder.name, 'result.tiff'))
                                    subprocess.Popen(pre_command, shell=shell).wait()
                                    del pre_command[:]
                                    pre_command.append('convert')
                                    pre_command.append(os.path.join(dirpathTempFolder.name, 'result.tiff'))
                                    pre_command.append('-profile')
                                    pre_command.append(os.path.join(self.icc_dir_textbox.text(), selected_screen_profile))
    
                            pre_command.append(os.path.join(dirpathTempFolder.name, 'result.tiff'))
                            subprocess.Popen(pre_command, shell=shell).wait()
                            if not os.path.isfile(os.path.join(dirpathTempFolder.name, 'result.tiff')):
                                inkex.utils.debug("Error. Missing result.tiff")

                        else:
                            if self.color_profile_choice_jpeg.isChecked():
                                pre_command = ['convert']
                                pre_command.append(os.path.join(dirpathTempFolder.name, 'result.tiff'))
                                pre_command.append('-profile')
                                pre_command.append(os.path.join(self.icc_dir_textbox.text(), selected_screen_profile))
                                pre_command.append(os.path.join(dirpathTempFolder.name, 'result.tiff'))
                                subprocess.Popen(pre_command, shell=shell).wait()
    
                        file_info = subprocess.Popen(['identify', os.path.join(dirpathTempFolder.name, 'source.png')], shell=shell, stdout=subprocess.PIPE).communicate()[0].decode('UTF-8')
                        if self.prepress_paper_cutmarks_check.isChecked():
                            bleedsize = (self.dpi_choice.value() / 96) * unittouu(str(self.prepress_paper_cutmarks_bleedsize_value.text()) + str(self.prepress_paper_cutmarks_bleedsize_choice.currentText()))
                            marksize = (self.dpi_choice.value() / 96) * unittouu(str(self.prepress_paper_cutmarks_marksize_value.text()) + str(self.prepress_paper_cutmarks_marksize_choice.currentText()))
                        else:
                            bleedsize = 0
                            marksize = 0
    
                        imposition_space = (self.dpi_choice.value() / 96) *unittouu(str(self.imposition_space_value.text()) + str(self.imposition_space_choice.currentText()))
    
                        image_width = []
                        for i in range(self.imposition_vertical_number_value.value()):
                            image_width.append(int(file_info.split(' ')[2].split('x')[0]))
    
                        image_height = []
                        for i in range(self.imposition_horizontal_number_value.value()):
                            image_height.append(int(file_info.split(' ')[2].split('x')[1]))
    
                        imposition_command = ['convert']
                        imposition_command.append(os.path.join(dirpathTempFolder.name, 'result.tiff'))
                        imposition_command.append('-extent')
                        imposition_command.append(str(sum(image_width) + (marksize*2) + (imposition_space * (len(image_width) -1))) + 'x' + str(sum(image_height) + (marksize*2) + (imposition_space * (len(image_height) -1))) + '-' + str(marksize) + '-' + str(marksize))
                        imposition_command.append(os.path.join(dirpathTempFolder.name, 'result-imp.tiff'))
                        subprocess.Popen(imposition_command, shell=shell).wait()
    
                        last_width = 0
                        last_height = 0
                        last_marksize = marksize
                        for width in image_width:
                            for height in image_height:
                                if not (last_width == 0 and last_height == 0):
                                    imposition_command = ['composite']
                                    imposition_command.append('-geometry')
                                    imposition_command.append('+'  + str(last_width + marksize) + '+' + str(last_height + marksize))
                                    imposition_command.append(os.path.join(dirpathTempFolder.name, 'result.tiff'))
                                    imposition_command.append(os.path.join(dirpathTempFolder.name, 'result-imp.tiff'))
                                    imposition_command.append(os.path.join(dirpathTempFolder.name, 'result-imp.tiff'))
                                    subprocess.Popen(imposition_command, shell=shell).wait()
    
                                last_height += height + imposition_space
                                last_marksize = 0
                            last_width += width + imposition_space
                            last_height = 0
    
                        if self.prepress_paper_cutmarks_check.isChecked():
                            cutmarks.generate_final_file(False, 
                                                         self.prepress_paper_cutmarks_inside_check.isChecked(),
                                                         list_of_color_modes_jpeg[self.color_mode_choice_jpeg.currentIndex()], 
                                                         image_width, 
                                                         image_height, 
                                                         imposition_space,
                                                         unittouu(str(self.prepress_paper_cutmarks_strokewidth_value.text()) + str(self.prepress_paper_cutmarks_strokewidth_choice.currentText())), 
                                                         bleedsize, 
                                                         marksize, 
                                                         dirpathTempFolder.name)
    
                            cut_marks_command = ['composite']
                            cut_marks_command.append('-compose')
                            cut_marks_command.append('Multiply')
                            cut_marks_command.append('-gravity')
                            cut_marks_command.append('center')
                            cut_marks_command.append(os.path.join(dirpathTempFolder.name, 'cut_mark.tiff'))
                            cut_marks_command.append(os.path.join(dirpathTempFolder.name, 'result-imp.tiff'))
                            cut_marks_command.append(os.path.join(dirpathTempFolder.name, 'result-imp.tiff'))
                            subprocess.Popen(cut_marks_command, shell=shell).wait()
    
                        if not os.path.isfile(os.path.join(dirpathTempFolder.name, 'result-imp.tiff')):
                            inkex.utils.debug("Error. Missing result-imp.tiff")
                                
                        jpeg_command.append(os.path.join(dirpathTempFolder.name, 'result-imp.tiff'))
    
                        if self.prepress_paper_settings_invert.isChecked():
                            jpeg_command.append('-negate')
    
                        if self.prepress_paper_settings_mirror.isChecked():
                            jpeg_command.append('-flop')
    
                        jpeg_command.append('-quality')
                        jpeg_command.append(str(self.quality_choice_dial_jpeg.value()))
    
                        jpeg_command.append('-colorspace')
                        jpeg_command.append(list_of_color_modes_jpeg[self.color_mode_choice_jpeg.currentIndex()])
    
                        if self.jpeg_interlace_option_jpeg.isChecked():
                            jpeg_command.append('-interlace')
                            jpeg_command.append(list_of_interlacing_jpeg[self.jpeg_interlace_choice_jpeg.currentText()])
    
                        if self.jpeg_optimize_option_jpeg.isChecked():
                            jpeg_command.append('-type')
                            jpeg_command.append('optimize')
    
                        if self.jpeg_noise_option_jpeg.isChecked():
                            jpeg_command.append('-evaluate')
                            jpeg_command.append(list_of_noise_jpeg[self.jpeg_noise_choice_jpeg.currentText()])
                            jpeg_command.append(str(self.jpeg_noise_ammount_jpeg.value()))
    
                        jpeg_command.append('-sampling-factor')
                        jpeg_command.append(self.jpeg_subsampling_choice_jpeg.currentText())
    
                        jpeg_command.append('-define')
                        jpeg_command.append('jpeg:dct-method=' + list_of_dct_jpeg[self.jpeg_dct_choice_jpeg.currentText()])
    
                        jpeg_command.append(os.path.join(dirpathTempFolder.name, 'result-imp.jpeg'))
                        
                        subprocess.Popen(jpeg_command, shell=shell).wait()
    
                def change_format(self):
                    self.general_options_panel_jpeg.setVisible(False)
    
                    if list_of_export_formats[self.format_choice.currentIndex()] == 'JPEG':
                        self.general_options_panel_jpeg.setVisible(True)
    
                    self.generate_preview()
    
                def change_color_mode_jpeg(self):
                    if list_of_color_modes_jpeg[self.color_mode_choice_jpeg.currentIndex()] == 'CMYK':
                        self.color_mode_title_tip_jpeg.setText(u'Recommended for graphic printing')
                        self.cmyk_advanced_manipulation_option_jpeg.setChecked(False)
                        self.cmyk_advanced_manipulation_option_jpeg.setEnabled(True)
                        self.cmyk_overblack_jpeg.setEnabled(False)
                        self.cmyk_overblack_jpeg.setChecked(False)
                        self.color_profile_choice_jpeg.setEnabled(True)
                        self.color_profile_choice_jpeg.setChecked(False)
                        self.document_color_profile_title_jpeg.setEnabled(True)
                        self.general_prepress_panel.setEnabled(True)
                    else:
                        self.cmyk_advanced_manipulation_option_jpeg.setEnabled(False)
                        self.cmyk_overblack_jpeg.setEnabled(False)
                        self.cmyk_overblack_jpeg.setChecked(False)
                        #self.color_profile_choice_jpeg.setEnabled(False)
                        self.color_profile_choice_jpeg.setChecked(False)
                        self.document_color_profile_title_jpeg.setEnabled(False)
                        self.general_prepress_panel.setEnabled(False)
                    if list_of_color_modes_jpeg[self.color_mode_choice_jpeg.currentIndex()] == 'CMY':
                        self.color_mode_title_tip_jpeg.setText(u'Recommended for specific print cases')
                    elif list_of_color_modes_jpeg[self.color_mode_choice_jpeg.currentIndex()] == 'RGB':
                        self.color_mode_title_tip_jpeg.setText(u'Recommended for use on screens')
                    elif list_of_color_modes_jpeg[self.color_mode_choice_jpeg.currentIndex()] == 'Gray':
                        self.color_mode_title_tip_jpeg.setText(u'Grayscale image')
    
                    self.generate_preview()
    
                def change_quality_live_jpeg(self):
                    self.quality_percent_title_jpeg.setText(str(self.quality_choice_dial_jpeg.value()) + '%')
    
                def jpeg_interlace_click_jpeg(self):
                    if self.jpeg_interlace_option_jpeg.isChecked():
                        self.jpeg_interlace_choice_jpeg.setEnabled(True)
                    else:
                        self.jpeg_interlace_choice_jpeg.setEnabled(False)
                    self.generate_preview()
    
                def jpeg_noise_click_jpeg(self):
                    if self.jpeg_noise_option_jpeg.isChecked():
                        self.jpeg_noise_choice_jpeg.setEnabled(True)
                        self.jpeg_noise_ammount_jpeg.setEnabled(True)
                    else:
                        self.jpeg_noise_choice_jpeg.setEnabled(False)
                        self.jpeg_noise_ammount_jpeg.setEnabled(False)
                    self.generate_preview()
    
                def cmyk_advanced_manipulation_click_jpeg(self):
                    if self.cmyk_advanced_manipulation_option_jpeg.isChecked():
                        self.cmyk_overblack_jpeg.setEnabled(True)
                        self.view_c_button.setVisible(True)
                        self.view_m_button.setVisible(True)
                        self.view_y_button.setVisible(True)
                        self.view_k_button.setVisible(True)
                        self.cmyk_overprint_black()
                        self.cmyk_advanced_manipulation()
    
                    else:
                        self.cmyk_overblack_jpeg.setEnabled(False)
                        self.cmyk_overblack_jpeg.setChecked(False)
                        self.view_c_button.setVisible(False)
                        self.view_m_button.setVisible(False)
                        self.view_y_button.setVisible(False)
                        self.view_k_button.setVisible(False)
                        self.generate_preview()
    
                def cmyk_overprint_black(self):
                    with open(os.path.join(dirpathTempFolder.name, 'original.svg'), 'r') as f:
                        if self.cmyk_overblack_jpeg.isChecked(): 
                            cmyk.generate_svg_separations(dirpathTempFolder.name, f.read(), True)
                        else:
                            cmyk.generate_svg_separations(dirpathTempFolder.name, f.read(), False)
    
                def cmyk_advanced_manipulation(self):
                    area_to_export = self.area_to_export()
                    cmyk.generate_png_separations(dirpathTempFolder.name, self.area_to_export(), self.dpi_choice.value(), False)
    
                    for color in ['C', 'M', 'Y', 'K']:
                        cmd = ['convert', 
                             os.path.join(dirpathTempFolder.name, 'separated' + area_to_export.replace(' ', '') + color + ".png"),
                             '-colorspace', 
                             'CMYK', 
                             '-channel', 
                             color,
                             '-separate',
                             os.path.join(dirpathTempFolder.name, 'separated' + area_to_export.replace(' ', '') + color + ".png")]
                        #inkex.utils.debug(cmd)
                        p = subprocess.Popen(cmd, shell=shell).wait()

                    self.cmyk_advanced_manipulation_view_separations()
    
                def cmyk_advanced_manipulation_view_separations(self):
                    area_to_export = self.area_to_export()
    
                    file_info = subprocess.Popen(['identify', os.path.join(dirpathTempFolder.name, 'source.png')], shell=shell, stdout=subprocess.PIPE).communicate()[0].decode('UTF-8')
    
                    image_size = file_info.split(' ')[2]
    
                    subprocess.Popen(['convert', '-size', image_size, 'xc:black',  os.path.join(dirpathTempFolder.name, 'empty.png')], shell=shell).wait()
    
                    final_command = ['convert']
    
                    if self.view_c_button.isChecked():
                        final_command.append(os.path.join(dirpathTempFolder.name, 'separated') + area_to_export.replace(' ', '') + 'C' + ".png")
                    else:
                        final_command.append(os.path.join(dirpathTempFolder.name, 'empty.png'))
    
                    if self.view_m_button.isChecked():
                        final_command.append(os.path.join(dirpathTempFolder.name, 'separated') + area_to_export.replace(' ', '') + 'M' + ".png")
                    else:
                        final_command.append(os.path.join(dirpathTempFolder.name, 'empty.png'))
    
                    if self.view_y_button.isChecked():
                        final_command.append(os.path.join(dirpathTempFolder.name, 'separated') + area_to_export.replace(' ', '') + 'Y' + ".png")
                    else:
                        final_command.append(os.path.join(dirpathTempFolder.name, 'empty.png'))
    
                    if self.view_k_button.isChecked():
                        final_command.append(os.path.join(dirpathTempFolder.name, 'separated') + area_to_export.replace(' ', '') + 'K' + ".png")
                    else:
                        final_command.append(os.path.join(dirpathTempFolder.name, 'empty.png'))
    
                    if not os.path.isfile(os.path.join(dirpathTempFolder.name, 'empty.png')):
                        inkex.utils.debug("Error. Missing empty.png")
    
                    final_command.extend(['-set', 'colorspace', 'cmyk'])
                    final_command.extend(['-combine', os.path.join(dirpathTempFolder.name, 'result.tiff')])
                    subprocess.Popen(final_command, shell=shell).wait()
    
                    self.generate_preview()
    
                def area_to_export(self):
                    if self.area_to_export_choice.currentIndex() == 1:
                        return 'export-area-drawing'
    
                    elif self.area_to_export_choice.currentIndex() == 2:
                        if self.area_to_export_idonly_check.isChecked():
                            return 'export-id:' + str(self.area_to_export_id_name.text()) + 'export-id-only'
                        else:
                            return 'export-id:' + str(self.area_to_export_id_name.text())
    
                    elif self.area_to_export_choice.currentIndex() == 3:
                        return 'export-area:' + str(self.x0_value.value()) + ':' + str(self.y0_value.value()) + ':' + str(self.x1_value.value()) + ':' + str(self.y1_value.value())
    
                    else:
                        return 'export-area-page'
    
                def change_area_to_export(self):
                    self.x0_value.setVisible(False)
                    self.y0_value.setVisible(False)
                    self.x1_value.setVisible(False)
                    self.y1_value.setVisible(False)
                    self.area_to_export_id_title.setVisible(False)
                    self.area_to_export_id_name.setVisible(False)
                    self.area_to_export_idonly_check.setVisible(False)
    
                    if self.area_to_export_choice.currentIndex() == 2:
                        self.area_to_export_id_name.setText(selected_object)
                        self.area_to_export_id_title.setVisible(True)
                        self.area_to_export_id_name.setVisible(True)
                        self.area_to_export_idonly_check.setVisible(True)
    
                    elif self.area_to_export_choice.currentIndex() == 3:
                        self.x0_value.setVisible(True)
                        self.y0_value.setVisible(True)
                        self.x1_value.setVisible(True)
                        self.y1_value.setVisible(True)
    
                    cmd = self.area_to_export() + ';export-dpi:' + str(self.dpi_choice.value()) + ';export-background-opacity:1;export-filename:' + os.path.join(dirpathTempFolder.name, 'source.png') + ';export-do'
                    cli_output = inkscape(os.path.join(dirpathTempFolder.name, 'original.svg'), actions=cmd)
                    #inkex.utils.debug(cmd)
                    if len(cli_output) > 0:
                        self.debug(_("Inkscape returned the following output when trying to run the file export; the file export may still have worked:"))
                        self.debug(cli_output)
    
                    subprocess.Popen(['convert', os.path.join(dirpathTempFolder.name, 'source.png'), os.path.join(dirpathTempFolder.name, 'source.tiff')], shell=shell).wait()

                    if not os.path.isfile(os.path.join(dirpathTempFolder.name, 'source.tiff')):
                        inkex.utils.debug("Error. Missing source.tiff")

                    self.generate_preview()
    
                def zoom_out(self):
                    self.preview_zoom += 0.1
                    self.generate_preview()
    
                    if int(self.preview_zoom * 100) == 200:
                        self.zoom_out_button.setEnabled(False)
                    self.zoom_in_button.setEnabled(True)
    
                    self.preview_zoom_title.setText(str(int(self.preview_zoom * 100)) + '%')
    
                def zoom_in(self):
                    self.preview_zoom -= 0.1
                    self.generate_preview()
    
                    if int(self.preview_zoom * 100) == 10:
                        self.zoom_in_button.setEnabled(False)
                    self.zoom_out_button.setEnabled(True)
    
                    self.preview_zoom_title.setText(str(int(self.preview_zoom * 100)) + '%')
    
                def cut_marks_insert_change(self):
                    if self.prepress_paper_cutmarks_check.isChecked():
                        self.prepress_paper_cutmarks_strokewidth_label.setEnabled(True)
                        self.prepress_paper_cutmarks_strokewidth_value.setEnabled(True)
                        self.prepress_paper_cutmarks_strokewidth_choice.setEnabled(True)
                        self.prepress_paper_cutmarks_bleedsize_label.setEnabled(True)
                        self.prepress_paper_cutmarks_bleedsize_value.setEnabled(True)
                        self.prepress_paper_cutmarks_bleedsize_choice.setEnabled(True)
                        self.prepress_paper_cutmarks_marksize_label.setEnabled(True)
                        self.prepress_paper_cutmarks_marksize_value.setEnabled(True)
                        self.prepress_paper_cutmarks_marksize_choice.setEnabled(True)
                        self.prepress_paper_cutmarks_inside_check.setEnabled(True)
    
                    else:
                        self.prepress_paper_cutmarks_strokewidth_label.setEnabled(False)
                        self.prepress_paper_cutmarks_strokewidth_value.setEnabled(False)
                        self.prepress_paper_cutmarks_strokewidth_choice.setEnabled(False)
                        self.prepress_paper_cutmarks_bleedsize_label.setEnabled(False)
                        self.prepress_paper_cutmarks_bleedsize_value.setEnabled(False)
                        self.prepress_paper_cutmarks_bleedsize_choice.setEnabled(False)
                        self.prepress_paper_cutmarks_marksize_label.setEnabled(False)
                        self.prepress_paper_cutmarks_marksize_value.setEnabled(False)
                        self.prepress_paper_cutmarks_marksize_choice.setEnabled(False)
                        self.prepress_paper_cutmarks_inside_check.setEnabled(False)
    
                    self.generate_preview()
    
                def format_preview_change(self):
                    if self.format_preview_check.isChecked():
                        self.resize(950, 600)
                        self.setMaximumSize(QtCore.QSize(950, 600))
                        self.setMinimumSize(QtCore.QSize(950, 600))
                        self.preview_panel.setVisible(True)
                        self.option_box.setGeometry(320, 120, 620, 435)
                        self.format_title.setGeometry(320, 70, 200, 15)
                        self.format_choice.setGeometry(320, 85, 200, 25)
                        self.export_button.setGeometry(740, 560, 200, 30)
                        self.format_preview_check.setGeometry(540, 85, 200, 25)
                    else:
                        self.resize(640, 600)
                        self.setMaximumSize(QtCore.QSize(640, 600))
                        self.setMinimumSize(QtCore.QSize(640, 600))
                        self.preview_panel.setVisible(False)
                        self.option_box.setGeometry(10, 120, 620, 435)
                        self.format_title.setGeometry(10, 70, 200, 15)
                        self.format_choice.setGeometry(10, 85, 200, 25)
                        self.export_button.setGeometry(430, 560, 200, 30)
                        self.format_preview_check.setGeometry(230, 85, 200, 25)
    
                    self.move(int((QtWidgets.QDesktopWidget().screenGeometry().width()-self.geometry().width())/2), int((QtWidgets.QDesktopWidget().screenGeometry().height()-self.geometry().height())/2))
    
                def export(self):
                    self.location_path = QtWidgets.QFileDialog.getSaveFileName(self, _(u"Save image"), os.environ.get('HOME', None), list_of_export_formats[self.format_choice.currentIndex()], options=QtWidgets.QFileDialog.DontConfirmOverwrite)

                    if not self.format_preview_check.isChecked():
                        self.generate_final_file()
    
                    if not str(self.location_path) == '':
                        result_imp = os.path.join(dirpathTempFolder.name, 'result-imp.' + list_of_export_formats[self.format_choice.currentIndex()].lower())
                        target_imp = os.path.abspath(self.location_path[0] + "." + self.location_path[1].lower())
                        if not os.path.isfile(result_imp):
                            inkex.utils.debug("Error. No result generated to export. The following files were created in temp dir:")
                            inkex.utils.debug(os.listdir(dirpathTempFolder.name))                   
                        else:
                            shutil.copy2(result_imp, target_imp)    
    
                def change_icc_dir(self):
                    self.icc_dir_textbox.setText(QtWidgets.QFileDialog.getExistingDirectory(self, 'Select Folder'))
    
            app = QtWidgets.QApplication(sys.argv)
            app.main = mainWindow()
            getattr(app.main, "raise")()
            app.main.show()
            app.main.activateWindow() #bring to front (required for Windows; but not for Linux)
            sys.exit(app.exec_())
            
            
        except Exception as e:
            self.msg(e)
        finally:
            #inkex.utils.debug(os.listdir(dirpathTempFolder.name))
            dirpathTempFolder.cleanup() #close temp dir

if __name__ == '__main__':
    OutputPro().run()