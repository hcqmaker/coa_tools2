@tool
extends EditorPlugin

const  DIALOG_WINDOW = preload("res://addons/coa_small_importer/coa_small_importer.tscn")
var dialog_win:Window = null
var btnMenuOpen:Button = null

func _enable_plugin() -> void:
	# Add autoloads here.
	pass


func _disable_plugin() -> void:
	# Remove autoloads here.
	pass

func _enter_tree() -> void:
	# Initialization of the plugin goes here.
	dialog_win = DIALOG_WINDOW.instantiate()
	dialog_win.visible = false
	EditorInterface.get_base_control().add_child(dialog_win)
	
	## show in  menu
	btnMenuOpen = Button.new()
	btnMenuOpen.text = "COA Small Import"
	btnMenuOpen.pressed.connect(self._open_dialog)
	add_control_to_container(CONTAINER_CANVAS_EDITOR_MENU, btnMenuOpen)
	pass

func _exit_tree() -> void:
	# Clean-up of the plugin goes here.
	if (btnMenuOpen):
		remove_control_from_container(CONTAINER_CANVAS_EDITOR_MENU, btnMenuOpen)
		btnMenuOpen.free()
		btnMenuOpen = null
	
	EditorInterface.get_base_control().remove_child(dialog_win)
	dialog_win.free()
	dialog_win = null
	pass


func _open_dialog():
	### center window
	dialog_win.popup_centered()
	
