
@tool  # carefull  is a tool need thiss
extends Window

@onready var file_dest_path: LineEdit = $root/VBoxContainer/to_path/fileDestPath
@onready var file_src_path: LineEdit = $root/VBoxContainer/from_path/fileSrcPath

@onready var log: RichTextLabel = $root/VBoxContainer/log

@onready var dlg_from: EditorFileDialog = $dlg_from
@onready var dlg_to: EditorFileDialog = $dlg_to
@onready var dlg_warning: ConfirmationDialog = $dlg_warning

var _bone_count = 0
var _sprite_count = 0

var _src_path:String = ""
var _dest_path:String = ""

var _node_scene:Node2D = null
var _skeleton:Skeleton2D = null
var _base_path:String = ""

#region

func _ready() -> void:
	get_window().files_dropped.connect(on_files_dropped)
	pass

func on_files_dropped(files:PackedStringArray) -> void:
	print(files)
	pass

func _on_close_requested() -> void:
	self.hide()
	
func _on_btn_cancel_pressed() -> void:
	self.hide()

func log_info(...args: Array) -> void:
	print(args)
	log.append_text(var_to_str(args) + "\n")
	
func _on_btn_to_path_pressed() -> void:
	if (file_dest_path.text != ""):
		dlg_to.current_path = file_dest_path.text;
	dlg_to.popup_centered_ratio();

func _on_btn_from_path_pressed() -> void:
	if (file_src_path.text != ""):
		dlg_from.current_path = file_src_path.text;
	dlg_from.popup_centered_ratio()

func _on_dlg_from_file_selected(path: String) -> void:
	file_src_path.text = path;

func _on_dlg_to_file_selected(path: String) -> void:
	file_dest_path.text = path;
	
func _show_warning(str:String) -> void:
	dlg_warning.dialog_text = str;
	dlg_warning.popup_centered_ratio();

func _await_filesystem_scan() -> void:
	var filesystem:EditorFileSystem = EditorInterface.get_resource_filesystem()
	while true:
		if filesystem.get_scanning_progress() >= 1.0:
			break;
		if not filesystem.is_scanning():
			break;
		await get_tree().process_frame
		
func _on_btn_import_pressed() -> void:
	log_info("_on_btn_import_pressed")
	var tmp_src = file_src_path.text;
	var tmp_dest = file_dest_path.text;
	
	if (tmp_src == "" or tmp_dest == ""):
		_show_warning("src path or dest path is Empty!!!")
		return;
		
	_do_import(tmp_src, tmp_dest);
	
#endregion
##########================ start import ===================
func _do_import(tmp_src:String, tmp_dest:String) -> void:
	
	_src_path = tmp_src;
	_dest_path = tmp_dest;
	
	## json
	var json_data:Dictionary = {}
	var json_path = _src_path
	if FileAccess.file_exists(json_path):
		var json = FileAccess.open(json_path,FileAccess.READ)
		json_data = JSON.parse_string(json.get_as_text())
		json.close()
	
	var node_2d = Node2D.new()
	node_2d.name = "Node2D"
	
	var skeletion = Skeleton2D.new()
	skeletion.name = "Skeleton2D"
	node_2d.add_child(skeletion)
	skeletion.owner = node_2d
	
	_skeleton = skeletion;
	_node_scene = node_2d;
	
	_sprite_count = 0
	_bone_count = 0
	
	var json_meshs:Array = json_data["meshs"];
	var json_nodes:Array = json_data["nodes"];
	var json_anims:Array = json_data["animations"];
	
	_base_path = "Skeleton2D/"
	
	var filesystem:EditorFileSystem = EditorInterface.get_resource_filesystem()
	var is_copy_image:bool = true;
	
	var tmp_dict_sprite_name2data = {} # sprite_name = {}s
	var tmp_dict_node_path2data = {} # node_path = {}
	
	_collect_sprite_mesh_data(json_meshs, tmp_dict_sprite_name2data, tmp_dict_node_path2data)

	# wait for copy image to dest path 
	if (is_copy_image):
		_copy_sprites(tmp_dict_sprite_name2data, _src_path, _dest_path)
		filesystem.scan();
		await _await_filesystem_scan()
		await get_tree().create_timer(1).timeout
	
	_generate_bones(json_nodes, node_2d, skeletion, tmp_dict_sprite_name2data, is_copy_image)
	_import_animations(json_anims, node_2d)
		
	var scene = PackedScene.new()
	scene.pack(node_2d)
	ResourceSaver.save(scene, _dest_path)
	
	await get_tree().process_frame
	filesystem.scan();
	
	log_info("------------------------finish import----------------")
	pass

###================================================
func _collect_sprite_mesh_data(meshs:Array, sprite_dict:Dictionary, node_path_dict:Dictionary) -> void:
	for mesh in meshs:
		var new_name = mesh["name"]
		var new_node_path = mesh["node_path"];
		sprite_dict[new_name] = mesh
		node_path_dict[new_node_path] = mesh
	pass

func _copy_sprites(sprite_dict:Dictionary, src_path:String, dest_path:String) -> void:
	var tmp_src_path:String = src_path;
	var tmp_dest_path:String = dest_path;
	var sprite_dir_path = tmp_dest_path.get_base_dir()
	
	var dir = DirAccess.open("res://")
	#for k,v in sprite_dict:
	for sprite_name in sprite_dict:
		var node = sprite_dict[sprite_name]
		### copy images to destination folder
		if tmp_src_path != "":
			if !(dir.dir_exists(str(sprite_dir_path,"/sprites"))):
				dir.make_dir(str(sprite_dir_path,"/sprites"))
			if dir.file_exists(str(tmp_src_path.get_base_dir(),"/",node["resource_path"])):
				var _src = str(tmp_src_path.get_base_dir(),"/",node["resource_path"])
				var _dst = str(sprite_dir_path,"/",node["resource_path"])
				dir.copy(_src,_dst)

			
func _generate_bones(nodes:Array, parent:Node2D, subparent:Node2D, mesh_dict:Dictionary, copy_images:bool = true, i:int = 0):
	var tmp_src_path:String = _src_path;
	var tmp_dest_path:String = _dest_path;
	var tmp_is_skeleton2D:bool = subparent.is_class("Skeleton2D")
	
	var dir = DirAccess.open("res://")
	for node in nodes:
		
		var new_node:Node2D
		var offset = Vector2(0,0)
		if "offset" in node:
			offset = Vector2(node["offset"][0],node["offset"][1])
		if node["type"] == "BONE":
			_bone_count += 1
			var new_bone:Bone2D = Bone2D.new()
			new_bone.set_autocalculate_length_and_angle(false)
			
			var new_name:String = node["name"]
			var new_tip:Vector2 = Vector2(node["position_tip"][0],node["position_tip"][1])
			var new_pos:Vector2 = Vector2(node["position"][0],node["position"][1])
			var new_rotation:float = node["rotation"]
			var new_scale:Vector2 = Vector2(node["scale"][0],node["scale"][1])
			var new_z:int = node["z"]
			
			new_bone.rest = Transform2D(Vector2(1.0, 0.0), Vector2(0.0, 1.0), new_pos)
			new_bone.set_meta("imported_from_blender",true)
			new_bone.set_name(new_name)
			
			new_bone.position = new_pos
			new_bone.rotation = new_rotation
			new_bone.scale = new_scale
			new_bone.z_index = new_z
			
			subparent.add_child(new_bone)
			new_bone.set_owner(parent)
			new_node = new_bone

		if node["type"] == "SPRITE" and not tmp_is_skeleton2D:
			#print("=", tmp_is_skeleton2D, ",", subparent,",",i)
			_sprite_count += 1
			### copy images to destination folder
			
			var new_name:String = node["name"]
			var new_tiles_x:int = node["tiles_x"]
			var new_tiles_y:int = node["tiles_y"]
			var new_node_path:String = node["node_path"]
			var new_frame_index:int = node["frame_index"]
			var new_offset:Vector2 = Vector2(node["pivot_offset"][0],node["pivot_offset"][1])
			var new_pos:Vector2 = Vector2(node["position"][0]+offset[0],node["position"][1]+offset[0])
			var new_roataion:float = node["rotation"]
			var new_scale:Vector2 = Vector2(node["scale"][0],node["scale"][1])
			var new_z:int = node["z"]
			
			var mesh_node:Dictionary = mesh_dict[new_name];
			
			var new_uv:Array = mesh_node["uv"]
			var new_vertices:Array = mesh_node["vertices"]
			var new_polygons:Array = mesh_node["polygons"]
			var new_weights:Array = mesh_node["weights"]
			
			#print("i:",i, " name:", new_name)
			var new_polygon:Polygon2D = Polygon2D.new()
			if copy_images:
				if tmp_src_path != "":
					var sprite_dest_path = str(tmp_dest_path.get_base_dir(),"/",node["resource_path"])
					if dir.file_exists(sprite_dest_path):
						### set sprite texture
						new_polygon.set_texture(load(sprite_dest_path))
						
			new_polygon.uv = _convert_to_uv(new_uv);
			new_polygon.polygon = _convert_to_polyon(new_vertices);
			new_polygon.polygons = _convert_to_polyons(new_polygons);
			
			for tmp_weight in new_weights:
				var tmp_bone_name:String = tmp_weight["name"];
				var node_path:String = tmp_weight["node_path"];
				var tmp_u_weight:Array = tmp_weight["weight"];
				new_polygon.add_bone(node_path, tmp_u_weight);
				#new_polygon.add_bone(node_path,_convert_to_weight(tmp_u_weight));
				
			new_polygon.set_meta("imported_from_blender",true)
			new_polygon.set_name(new_name)
			#new_polygon.set_hframes(new_tiles_x)
			#new_polygon.set_vframes(new_tiles_y)
			#new_polygon.set_frame(new_frame_index)
			#new_polygon.set_centered(false)
			new_polygon.set_offset(new_offset)
			new_polygon.position = new_pos
			new_polygon.rotation = new_roataion
			new_polygon.scale = new_scale
			new_polygon.z_index = new_z
			

			subparent.add_child(new_polygon)
			new_polygon.set_owner(parent)
			new_node = new_polygon;
			
			new_polygon.skeleton = _get_path_to_skeleton(new_node_path)
			#
			#var new_sprite:Sprite2D = Sprite2D.new()
			#if copy_images:
				#if tmp_src_path != "":
					#var sprite_dest_path = str(tmp_dest_path.get_base_dir(),"/",node["resource_path"])
					#if dir.file_exists(sprite_dest_path):
						#### set sprite texture
						#new_sprite.set_texture(load(sprite_dest_path))
						#
			#new_sprite.set_meta("imported_from_blender",true)
			#new_sprite.set_name(new_name)
			#new_sprite.set_hframes(new_tiles_x)
			#new_sprite.set_vframes(new_tiles_y)
			#new_sprite.set_frame(new_frame_index)
			#new_sprite.set_centered(false)
			#new_sprite.set_offset(new_offset)
			#new_sprite.position = new_pos
			#new_sprite.rotation = new_roataion
			#new_sprite.scale = new_scale
			#new_sprite.z_index = new_z
#
			#subparent.add_child(new_sprite)
			#new_sprite.set_owner(parent)
			#new_node = new_sprite;
		
		if "children" in node and node["children"].size() > 0:
			i+=1
			_generate_bones(node["children"], parent, new_node, mesh_dict, copy_images, i)
	pass
	
func _import_animations(animations:Array, owner:Node2D) -> void:
	if (not animations or len(animations) <= 0):
		return;
		
	var anim_player:AnimationPlayer = AnimationPlayer.new()
	anim_player.callback_mode_process = AnimationMixer.ANIMATION_CALLBACK_MODE_PROCESS_PHYSICS
	owner.add_child(anim_player)
	anim_player.set_owner(owner)
	anim_player.set_name("AnimationPlayer")
	
	var anim_lib:AnimationLibrary = AnimationLibrary.new()
	
	log_info(str("Animation Count: ",animations.size()))
	if animations.size() > 0:
		log_info(str("#### Animations ####"),0,true)
	for anim in animations:
		
		var anim_name:String = anim["name"]
		var anim_length:int = anim["length"]
		var anim_fps:int = anim["fps"]
		
		log_info(str("> ", anim_name,":   length - ", anim_length, "    fps - ", anim_fps))
		# TODO 创建设置初始值 RESET  应该如何设置
		if (anim_name == "Restpose"): # RESET
			anim_name = "RESET"
			pass
		##  TODO 设置为全局动画？？？？
		var anim_data = Animation.new()
		anim_data.loop_mode = false;
		anim_data.set_length(anim_length)
		
		for key:String in anim["keyframes"]:
			var track_dict = anim["keyframes"][key]
			var idx = anim_data.add_track(Animation.TYPE_VALUE)
			#var idx = anim_data.add_track(Animation.TYPE_BEZIER)
			
			if key.contains(":transform/pos"):
				var path:String = key.replace(":transform/pos", ":position")
				anim_data.track_set_path(idx, _base_path + path)
				for time in track_dict:
					var value = track_dict[time]["value"]
					anim_data.track_insert_key(idx, float(time),Vector2(value[0],value[1]))
			elif key.contains(":transform/scale"):
				var path:String = key.replace(":transform/scale", ":scale")
				anim_data.track_set_path(idx, _base_path + path)
				for time in track_dict:
					var value = track_dict[time]["value"]
					anim_data.track_insert_key(idx,float(time),Vector2(value[0],value[1]))
			elif key.contains("modulate"):
				anim_data.track_set_path(idx,_base_path +  key)
				for time in track_dict:
					var value = track_dict[time]["value"]
					anim_data.track_insert_key(idx,float(time),Color(value[0],value[1],value[2],1.0))
			elif key.contains(":transform/rot"):
				var path:String = key.replace(":transform/rot", ":rotation")
				anim_data.track_set_path(idx, _base_path + path)
				for time in track_dict:
					var value = track_dict[time]["value"]
					anim_data.track_insert_key(idx,float(time),rad_to_deg(value))
			elif key.contains(":frame") or key.contains(":z/z"):
				anim_data.track_set_path(idx, _base_path + key)
				anim_data.track_set_interpolation_type(idx, Animation.INTERPOLATION_NEAREST)
			else:
				anim_data.track_set_path(idx, _base_path + key)
				anim_data.track_set_interpolation_type(idx, Animation.INTERPOLATION_LINEAR)
			
		anim_lib.add_animation(anim_name, anim_data)
		
	var anim_library_name:String = "animations"
	anim_player.add_animation_library(anim_library_name, anim_lib)
	


###----------------------------------------------------------
func _get_path_to_skeleton(node_path:String) -> String:
	var num:int = node_path.get_slice_count("/");
	var rs:String = ".."
	if num > 1:
		for i  in range(num-1):
			rs += "/.."
	return rs
	
func _convert_to_polyon(src:Array) -> PackedVector2Array:
	var rs:PackedVector2Array = PackedVector2Array()
	for i in range(0, len(src), 2):
		rs.append(Vector2(src[i], src[i+1]));
	return rs;
	
func _convert_to_uv(src:Array) -> PackedVector2Array:
	var rs:PackedVector2Array = PackedVector2Array()
	for i in range(0, len(src), 2):
		rs.append(Vector2(src[i], src[i+1]));
	return rs;

## polygon point index
func _convert_to_polyons(src:Array) -> Array:
	var rs = [];
	for vv in src:
		rs.append(PackedInt32Array(vv))
	return rs;
	
#func _convert_to_weight(src:Array)-> PackedFloat32Array:
	#var rs:PackedFloat32Array = PackedFloat32Array();
	#
	#return rs
