#

## 0.9.18+patch.5

> 2025-07-03

- Boolean tool
	- support MeshCut operation
		- NOTE: mesh cuts work on the original mesh, so are best suited for objects with no or minimal mod stacks
	- fix previously adjusted gap strength being re-initialized when switching away from GAP boolean and back to it again

* AddObject tool
	- support MeshCut operation
		- when meshcutting an inset that has children, re-parenting the children to the boolean host, as the operand object will be removed in the process of the mesh cut
	- generalize and simplify boolean setup, toggling in and out of it, changing the method, etc.
		- for SPLIT and MESHCUT booleans force select the boolean host for better intersection preview
	- generalize how asset meta data is stored internally
	- add fallbacks for manifold insets set up in 4.5, but brought into 4.4 and earlier

* CreateAsset tool
	- for SPLIT boolean insets, support new `ignore_secondary_boolean` property
		- see new 3 split insets examples for the difference in behavior
	- support inset creation with MeshCut as the operation
	- rework setup panel a bit and how the various props interact and depend on each other
	- introduce `inset_version` prop to distinguish assets created in 4.5 vs 4.4 and earlier due to the potential of Manifold booleans being present

* EvaluatedExtract tool
	- support removing selection boundary on the active object, toggle via `R`
		- useful if you previously added a mesh cut for the sole reason to extract a specific part of the mesh
	- prevent fill angle going below 0
	- decrease/increase angle in 1° steps when going below 5°

- TransformCursor
	- add option in addon prefs to always snap when dragging, so there's no need to hold `CTRL`
	- called from MACHIN3tools Cursor and Origin pie
		- only set *Transform Orientation* when setting Cursor Rotation only
		- and only set *Transform Pivot* when setting Cursor Location only
	- mention in HUD if Transform Pivot/Orientation is set
	- fix radial array setup, when object origin is exactly in cursor

* PointCursor tool
	- support setting Cursor Orientation
		- toggle via `T` like in TransformCursor tool
	- expose `set_transform_orientation` default to addon prefs

* HyperBevel
	- remember `loop_angle` from one op call to the next
	- always ensure geo gizmos are shown (when enabled), no matter the polycount

- ApplyAll tool
	- fix exception encountering geo node mod with panels
- ToggleAll tool
	- fix exception when calling with ALT modkey (toggle objects) mode, when mod objects are not on viewlayer

- PushFace tool
	- fix object losing location on redo

* PickObjectTree tool
	- avoid showing invalid child level for mod object parented to another host

* addon prefs
	- make more "Outside" keymaps available for and expose each one under Tool Defaults under Settings tab
		- PickHyperBevel tool
		- HyperCut tool
		- HyperBend tool
		- PickObjectTree tool
	- expose them as "Regular Keymaps" under the keymaps tab too
	- support finding missing keymaps and restoring them

* fix exception repeatedly deactivating and re-activating the addon

- Example Assets
	- add 3 new Split insets
	- add 2 new MeshCut insets
	- add 2 new Difference insets
	- add HookMilledHole
	- update some inset names, remove old ones used for testing


## 0.9.18+patch.4

> 2025-06-19

- TransformCursor and PointCursor tools
  - visualize snap increment coords in 3D view when grid snapping on a smaller scale (adjust by scrolling while grid snapping)
    - limit it to 2 and draw it as 1/10 and 1/100 in the HUD and statusbar too now

  - tweak behavior when invoked from MACHIN3tools' _Cursor and Origin_ pie, better mirroring MACHIN3tools behavior
    - support setting only Location when invoked with `ALT` being held
    - support setting only Rotation when invoked with `CTRL` being held
    - NOTE: both snap automatically and always
    - only allow cursor transformation, no objects
    - simplify HUD and statusbar accordingly

  - support setting Blender's transform pivot and orientation, toggle via `T`
    - disabled by default, but can be default-enabled in addon prefs
    - can be set up to only do this when invoked from MACHIN3tool's _Cursor and Origin_ pie

  - disable showing _Absolute Coords_ by default, toggle via `A` as before
    - can be default-enabled in addon prefs too

  - remember previous _Grid Increment_ setting when re-invoking tool
  - remember previous _Ignore Snapped Rotation_ setting, when re-invoking tool

  - significantly improve performance transforming huge assembly (instance collection) objects via `Q` or `S` toggles

  - improve recovering from **cancelled** native Translate/Rotate pass-through (by holding `CTRL` while invoking the Translate or Rotate gizmos)
    - only a single `ESC` press is required now to reveal the HC gizmos again in such a case
  * avoid odd behavior when view is locked to the cursor

- PointCursor tool
  - significantly improve performance transforming huge assembly (instance collection) objects via `Q` or `S` toggles

- HyperBevel
  - introduce `CTRL + B` keymap that works when HyperCursor tools is not active
    - deactivated by default
    - enable under _Settings_ tab > Addon > Tool Defaults > HyperBevel
  - lower default loop selection angle from 40 to 30 degrees
    - adjust by holding `G` as before

- HyperBevel, HyperCut and likely other tools
  - fix precision issues while in ORTHO view while also using a massive _clip_end_ value

- HyperCut tool
  - fix exception introduced in patch.2 when _bbox_ or _cursor plane_ drawing into _face plane_
  - tweak statusbar cursor plane axis buttons

- AdjustArray tool
  - fix exception drawing in-between points for centered FIT arrays, when lowering count to 3

- MatchSurface tool
  - fix issue when active object has mods, where index face detection went wrong
  - fix exception when index face has 2-edged verts

- Focus and FocusProximity tools
  - pop a message when view is locked to the cursor, that only zooming works

- ScaleFace and MoveFace tools
  - fix geo gizmos not updating when `ALT` repeating

- Tool Header
  - fix exception when generic gizmo reference becomes invalid in memory

- Geometry Gizmos
  - use less-dense 48 (tri-)coord geo for Edge Gizmos vs the previous 132 (tri-)coord ones

- addon prefs
  - introduce boxes below opened panels to better group and separate things again

## 0.9.18+patch.3

> 2025-06-07

- AddPipe tool
  - fix exception when adjusting global radius via `W` key, accidentally introduced in patch.2
- AdjustPipe tool
  - support extending multiple curve splines at once, not just the first
  - fix exception adjusting single point curves

- HyperCut
  - fix rare exception when snapping while toggling into depth adjustment mode while in ortho view
- SnapRotate tool
  - determine axis ring HUD based on rotational axis dimensions, not an average of all

- in assetbrowser, only draw import method warning, when HyperCursor tool is active
- support point drawing in vulkan and metal in Blender 4.5

## 0.9.18+patch.2

> 2024-06-03

### Blender

- in Blender 4.5
  - default to MANIFOLD solver for all booleans
    - AddObject, Add Boolean, HyperCut, HyperBevel and CreateAsset tools
  - add ManifoldBooleanConvert tool in sidebar panel
    - turn all boolean mods in the stack into MANIFOLD ones
    - useful to update models created previously, good to see the performance and stability changes too

### Tools

- Blendulate tool
  - bring over latest changes from CURVEmachine
    - support Blendulating cyclic spline ends
    - support redoing via Shift + R
    - further modernize statusbar
- TransformCursor tool
  - grid snapping
    - support _move snapping_ on grid, previously you could only do it when _drag snapping_
    - show grid increments in HUD when snapping on grid
    - fix statusbar to properly show grid increments, whenever you snap to the grid, not just when arraying
  - move selection or selection with cursor
    - support disabling selection flip via `X` key, when _drag snapping_ selection `S` or selection and cursor `C`
  - fix hang when snapping on instance collection object, that has its wire objects also linked on the view layer
  - fix tooltip mentioning mod keys, when invoked from MACHIN3tools Cursor and Origin pie
    - here it only ever drags the cursor
    - requires MACHIN3tools 1.12.1
  - fix selection not being previewed when resetting cursor origin (to world) via `G` or `W`
- SnapRotate tool
  - ignore mirror and array mods, when determining axis ring HUD size (based on object size)
- AddObjectAtCursor tool
  - update `ALT` repeat tooltip
- PushFace tool
  - actually do allow snapping on "connected other verts" after all (see [patch.1 before](#0918patch1))
    - they are stationary, and it's only the edges that should be avoided
  - support sliding face _a little_
    - it showed in the HUD before, but ever worked
- HyperCut
  - fix exception when setting draw plane from face on mirror mod's instance
- DuplicateObjectTree tool
  - fix issue of leaving some mod objects revealed if they aren't parented and where _severely hidden_ before

- HideWireObjects tool
  - improve _\_Wires_ collection creation
    - support multiple per-blend file, one per scene
    - make it blue to contrast with the green and orange _\_Assemblies_ collections in MACHIN3tools
  - avoid hiding MACHIN3tools' group anchors
- HyperBevel tool
  - fix rare exception in gizmo group initiation
- EditHyperBevel tool
  - fix exception when editing cyclic HyperBevels

- HyperMod tool
  - fix exception when `CTRL + A` applying mods while MESHmachine is not installed

- AdjustCylinder tool
  - avoid messing up geo when encountering torus geo, abort instead
- AddPipe tool
  - fix exception adjusting radius segment count due to typo
  - disable debug output to catch point spam issue
- AdjustPipe tool
  - fix exception when cancelling cyclic pipes
- AdjustArray tool
  - fix exception drawing radial center array instance coords when going down to count of 2
  - fix exception toggling a radial center array into a full array
- ApplyAll tool
  - fix rare exception when applying mods for multi-object selections (from mod panel)
- FocusProximity tool
  - prevent getting stuck at a proximity value of 0

### Gizmos

- GeoGizmoSetup tool
  - increase angle threshold for redundant edge removal (so remove more of them)
- Object Button Gizmos
  - exclude all DECALmachine objects - not just decals - from getting these gizmos, so including trimsheet/atlas setup objects, and individual trim helper objects on these
  - exclude MEShmachine's plug handle objects

### Menus

- Face pie
  - with PUNCHit 1.3 installed, support PUNCHit invocation from object mode

### Panels

- Object Popup Panel
  - expose HyperBevel mode switch prefs
    - NOTE: still toggles the addon prefs, not a per-hyperbevel prop

- sidebar panel
  - add dedicated support and documentation sub-panels
    - both toggled via single ❓ button in header, like in PUNCHit, CURVEmachine, MACHIN3tools
  - gizmos sub-panel
    - expose Geo Gizmo Setup buttons

### Internal

- add Get Support tool
  - show in addon prefs
  - show in sidebar panel
- bring over modernization from MACHIN3tools and PUNCHit
  - object visibility handling
  - statusbars
    - draw all available numeric input keys
    - enhance precision indicator for tools that allow changing it via `SHIFT` _a little_ or `CTRL` _a lot_
  - update various utility functions

- yank out automatic asset _import method_ change
  - draw a warning/button in the asset browser header instead, when LINK or APPEND_REUSE are used
- update HyperCursor Manager object
  - use classmethods
  - add icon management
- linked object handling
  - HyperMod tool
    - prevent exception when trying to `CTRL + A` apply mods on object that is linked
  - ApplyAll tool
    - poll against linked objects
  - point out if active object is linked or has linked mesh
    - in HC's Object Popup panel
    - in Blender's modifiers panel
  - manage_geo_gizmos() handler
    - avoid checking linked objects

- addon prefs
  - tweak keymap display
  - re-layout a few parts
  - integrated updater
    - support updating x.x.x+patch.x styled versions
      - NOTE: will work for the next patch only

- fix a number of exceptions when invoking operator tooltips from operator search panel
- fix odd Blender crash, when deactivating MACHIN3tools Mirror tool, while HC is registered, and then opening operator search menu??

## 0.9.18+patch.1

> 2024-02-14

- HyperBevel tool
  - fix issue when re-creacting cutter geo after leaving edit mode, when cutter object was deselected while in edit mode
  - also support bringing multiple HyperBevel cutters into edit mode at once
  - in adjustment pass, avoid accepting keyboard inputs and showing their keys in the statusbar, while gizmos are highlighted
    - except for `SHIFT` and `R` while an extend gizmo is highlighted
    - `R` is also used to toggle _Realtime_ mode - while no gizmo is highlighted
- Pushface tool
  - avoid snapping on verts and edges connected to the face that is being pushed
  - fix geo gizmos not updating when `ALT` repeating while `SHIFT` is being held too

- addon preferences
  - fix exception in keymaps tab when encountering invalid Toobar Popup keymap item

## 0.9.18

> 2024-02-10

### Blender

- raise minimum Blender version to 4.2

### New Additions

- add HyperBevel 2
  - completely rewritten from the ground up for better UX
  - 3 stepped process
    - selection
      - toggle weld-preprocessing via `ALT`
        -hold `T` to adjust weld threshold
      - loop select via `SHIFT`
        - hold `G` to adjust loop angle
      - use `SPACE` to quickly finish with previous HyperBevels settings
    - width dragging
      - drag out initial bevel width
      - batch toggle sweep alignment, depending on topological conditions
    - gizmo adjustment
      - extend the ends of non-cyclic cutters
      - toggle individual sweep edge alignments, depending on topological conditions
        - hold `SHIFT` to affect neighboring sweeps
      - fine-tune bevel width
      - change segment count and toggle chamfer and realtime preview
      - drop bevel profiles from the asset browser
      - use `ALT + SCROLL` to adjust HyperBevel placement in mod stack
  - automatically create smooth shaded cutter, when active object is smooth shaded
  - use `SPACE` to finish with the cutter hidden
  - use `LMB` to finish with the cutter selected
  - use `TAB` to finish into cutter edit mode
  - always sort new mod after last Split boolean in the stack, if present
  - easy cutter editing modification afterwards, simply by switching edit/object modes - HC does the rest automatically
    - NOTE: there is no more need to re-run HyperBevel from edit mode now, when you chose to make an adjustment in edit mode
    - remove legacy edit mode `SHIFT + B` HyperBevel keymap accordingly
- add (flick) Boolean tool
  - with 2+ objects sleected, invoke via `B` keymap
    - or via new Boolean button gizmo
  - pick boolean operation from the flick circle menu
    - adjust what kinds of operations appear in the flick circle menu in the addon prefs, by default all 5
      - Difference, Union, Intersect, Split, Gap
        - Gap boolean uses custom geo node "Source" mod, to replicate boolean operand object's mod stack
    - scroll to change the active object of the boolean operation
    - use `SPACE` or drag out of the circle to finish with the cutter hidden
    - use `LMB` to finish with the cutter selected
    - use `TAB` to finish into HyperMod

- add Hype and Unhype tools
  - easily turn objects created outside of HC into _hyper objects_
    - gives access to geometry and object button gizmos
  - Hype is accessd from new **⏻** button gizmo
  - Unhype is accessed from Object and Modifiers panel

- add Link and Unlink tools
  - accessed via **🔗** Link button gizmos
- add Parent and UnParent tools
  - accessed via Parent button gizmos
  - when Parenting, leave only the parent active and selected

### Gizmos

- add dedicated set of Button gizmos for multi-object-selections to
  - hype objects
  - parent objects
  - link object's meshes
  - add booleans
- add Button gizmos on active to
  - unparent object
    - use `ALT` to reveal parent instead
  - unlink an object's mesh
    - use `ALT` to reveal other objects using the linked mesh instead
- Geometry gizmos
  - support hyper ring selecting edge gizmos directly via `SHIFT + CTRL + LMB`
    - NOTE: via the dedicated Select button, it's still only `CTRL`

### Add Object

- AddObjectAtCursor tool
  - indicate in HUD, if there is a history entry for the object (and so the previous object's size can be reused via `MMB`)
  - draw surface plane, which helps understanding the placement
  - add cursor history entry whenever you create a cylinder
    - adjustable in addon prefs, and can optionally be done for Cube's and Assets too, or not at all
  - update rounded cube and cylinder creation (`R` toggle)
    - in 4.2:
      - always use one vg bevel for cubes and remove support for multiple ones by subdividing the cube's mesh
      - always use 2 vg bevels for cylinders (top and bottom)
    - in 4.3, taking advantage of edge weight bevels now
      - support cubes with 1, 2, or 3 bevels mods
      - support cylidners with 1 bevel mod now
  - when adding assets with subsets on objects with mirror mods, preview mirrored subsets by drawing their wires
  - expose number keys to statusbar for subdivision or bevel mod count adjustments
  - when doing booleans for cubes and cylinders, set object's display type based on whether object is in range of boolean host
  - add `W` keymap to toggle wireframe overlays, use `SHIFT + W` now to toggle boolean display type cycling
  - prevent accidentally adding objects to hidden layer collections, when one is active in the outliner
  - fix issue with boolean solver options in redo panel
  - fix issues when redoing where boolean setup would not happen
  - avoid Blender's _using fallback_ warning in system console, when trying to boolean microscopic objects (due to the size not having been dragged out yet)

### Hype

- HyperCut
  - refactor major parts of it, improving performance on dense meshes and complex mod stacks considerably
  - rework how depth and width limiting/adjusting works
    - use mouse movement instead of scrolling now
    - tap `ALT` to flip width or depth limit from one side to the other
  - always sort new mod after last Split boolean in the stack, if present
  - add workaround for Blender's object origin-loss-on-redo bug
  - in _apply mode_ with MESHmachine installed, stash the cutter
- HyperBend
  - add workaround for Blender's object origin-loss-on-redo bug
  - flesh out statusbar some more
    - indicate `LMB` action when highlighting one of the gizmos
    - indicate segment count, and adapt to mouse position relative to the cursor on the screen
    - preview highlighted gizmos, and what they do
  - show pre-bend wire while adjusting limit, even while bend angle is zero
  - avoid bending mirror objects, when self.affect_children is set and mirror mod uses object to mirror across

- EditHyperBevel tool
  - support toggling smooth shading via `S` key
  - support `ALT` _profile-repeating_ previous HyperBevel (created via HyperBevel or adjusted via EditHyperBevel)

- ExtendHyperBevel tool
  - show wire of non-evaluated parent object
    - helpful to see actual mesh boundaries for heavily booleaned object

### Transform tools

- TransformCursor tool
  - support transforming the object selecvtion when dragging or moving the cursor, based on the initial cursor location and orientation
    - great way to place a selection exactly where you want it to sit
      - when translating, or when draggin without snapping on anything, or when snapping while ignoring snapped cursor rotation - do a simple translation
      - when dragging and snapping do a more advanced transformation that allows aligning the selection relatively based on the initial (snapped) cursor with the new snapped cursor
        - this creates a face-to-face alignment, or face-to-edge, or whatever else you want to "snap" to each other
    - use `Q` or `S` to toggle this on - `S` if you only want to transform the selection, `Q` if you want to transform both
    - selection get's previewed in the new location by drawing its wire
  - support shapping cursor on instance collections / assembly assets
  - hyper arrays
    - fix not being able to array wire objects
    - prevent exception when arraying selection including empties

- Point Cursor tool
  - support pointing the X axis to an edge using `CTRL`
  - similar to TransFormCursor, support pointing a selection via `S` key
    - like for the cursor itself, Z axis gets pointed based on chosen face, while X and Y axes get pointed based on chosen edge

- CastCursor tool
  - support casting on instance collections
  - mention _Grid Align_ in HUD not _Surface Align_ when cast hits grid while _Surface Align_ is enabled

- SnapRotate tool
  - draw ring to further emphasize the view-based-chosen rotation axis
  - also allow lowering snap angle in 1° steps down 1°, once you reach 5°

### Manage

- HyperMod tool
  - support previewing 3+ corner bevels
    - I still don't recommend setting them up though :)
  - support unpinning of pinned mods using `P`
  - automatically unpin mod, if you attempt to move another to its location
  - show warning in HUD when current mod stack order differs compared to how HC would sort it
  - show alternate warning when mod sorting is disabled
  - with sorting disabled also disable modifier prefix addition (+ or -) when moving mods
  - for Catmull-Clark SubD's support toggling _PRESERVE_CORNERS boundary smooth_ prop via `C` key - aka _Keep Corners_
  - support selecting and toggling mirror objects
  - indicate and support selecting _severely hidden_ mod objects, which come in 3 flavors:
    - not in scene, not on view layer (in excluded collection), in hidden collection(s) only

- PickHyperBevel tool
  - support changing segment count simply by highlighting gizmo and scrolling
    - so without even invoking EditHyperBevel via `LMB`
  - support toggling chamfer too - via `C`
  - make cutter selection work how it's done in PickObjectTree tool
    - `S` to select and finish the tool
    - `SHIFT - S` to select multiple
    - NOTE: no `ALT` to _affect all_ yet though
  - add `CTRL - S` to select and finish into edit mode
  - indicate and support _severely hidden_ hyper bevel objects, which come in 3 flavors:
    - not in scene, not on view layer (in excluded collection), in hidden collection(s) only
- Pick Object Tree tool
  - indicate and support selecting _severely hidden_ mod objects, which come in 3 flavors:
    - not in scene, not on view layer (in excluded collection), in hidden collection(s) only
  - make hiding of active's wire children on tool invocation optional in addon prefs

- RemoveUnusedBooleans tool
  - refactor to avoid impression of initial freezing, show progress HUD instead
  - fix exception when launched from the properties panel
- PickObjectTree tool, RemoveUnusedBooleans tool, cursor history visualization
  - redo completely how labels in the HUD are placed in relation to the button gizmos that are also shown
    - support all kinds of combinations of system scaling, Blender's UI and gizmo scaling, as well as HyperCursor HUD scaling
- HideWireObjects tool
  - support not just hiding visible wire objects as before, but sorting all scene wire objects into a dedicated \_Wires collection
    - IF objects are not in any other user created collection
    - can be disabled in addon prefs, to restore the legacy _just-hide-behavior_
  - pop a message when objects where hidden, or sorted into `_Wires` collection
- DuplicateObjectTree tool
  - handle _severely hidden_ objects
    - only duplicate or instance 2 of the 3 flavors however
      - objects in excluded collections
      - objects in hidden collections
  - avoid duplicating mirror objects in the tree unless `SHIFT` is being held

### Curve tools

- Blendulate tool
  - update to latest state in CURVEmachine 1.3
    - support NURBS `use_endpoint_u`, `order_u` and `resolution_u` props
      - previously these got lost when blendulating a _NURBS_ spline, now they are maintained
  - support `ALT` for merging (in addition to existing `M` key)
- AddPipe tool
  - support finishing directly into AdjustPipe tool using `TAB`
- AdjustPipe tool
  - support toggling to NURBS curve via `Q` key

### Edge tools

- BevelEdge tool
  - Blender 4.3 support edge weight based beveling
    - toggle via `E` key
    - vgroup based bevels remain the default, as they have better stacking behavior
    - use edge weights in cases where vgroup bevels affect undesired edges
  - ensure toggling loop selection via `SHIFT` only uses gizmo edges
  - support tension adjustment for mesh and mod bevels using `T`

### Face tools

- ExtrudeFace tool
  - support and default to making mesh manifold
    - this option is available when the hyper selected faces' border edges are the same as all existing non-manifold edges
      - think of a simple plane or circle being extruded - will be transformed into manifold cube or cylinder accordingly
- MatchSurface tool
  - preview the matched face's location and orientation
- Push Face tool
  - improve performance when pushing faces of boolean operand objects, by avoiding mod stack evaluation
  - support pushing _a little_ via `SHIFT`
- ExtractFace tool
  - in basic (non-evaluated) mode (invoked from Face pie) clear the hyper selection on the original
  - fix exception when fill-selecting and encountering edges with more than 2 faces
  - fix exception trying to create preview/selection coords, when nothing or an object other than the active was hit by ray cast
- Move Face tool
  - fix issue where amount was not properly displayed
  - fix issue where intering numeric amount would not properply translate based on previous interactive adjustment

### Adjust tools

- AdjustDisplace tool
  - use `ALT + SCROLL` to pick among potentially multiple Displace mods in the local stack or on potential _remote objects_
    - NOTE: split and gap boolean cutters' Displace mods can be adjusted remotely from their respective non-wire objects for convenience
  - draw SPLIT or GAP wire when adjusting remote Displace mods

### misc

- BooleanTranslate and BooleanDuplicate macros
  - rewrite, simplify, optimize
  - remove mirror mods that used the original parent, when the parent object changed (moving inset from one to another object for instance)
- ApplyAll tool
  - fix MESHmachine exception when creating stashes due to MM update
  - disable backup creation
    - to be re-designed in 0.9.19

### Assets

- assets
  - add 2 spot weld insets
  - turn off ray visibility for arrows on hook insets

### Panels

- Sidebar panel
  - add tools panel
    - expose major tools and macros in a single place, grouped togethere, similar to the keymaps panel
  - keymaps panel
    - support drawing 4.3's extra-wide keymap icons
    - draw keymaps dimmed when they have been deactivated
- Object and Modifiers panel
  - show mesh instance count and allow unlinking by clicking on it
  - support disabling HyperCursor's mod sorting for active object
    - disabled automatically when hyping objects created outside of HC, with mod stacks whose sorting differs compared to how HC would sort it
  - with mod sorting enabled expose Sort tool, when current mod stack order is different than how HC would sort it
    - NOTE: mod sorting is otherwise run automatically by tools like HyperCut or HyperBevel to place their mods in the stack
  - change name of Duplicate button to _Duplicate Tree_
  - disable backup retrieval
    - to be re-designed in 0.9.19
  - Object button gizmo
    - when `CTRL` clicking it to force mod sorting, pop a fading message
- Geo Gizmo panel
  - expose buttons to Setup and Clear gizmos
    - previously this was only done via mod key clicking on the button gizmo, that opens the panel

### Pies

- AddObject pie
  - draw asset icon, if there is an active asset
    - NOTE: can't click on it unfortunately, only serves as a preview of the selected asset

### preferences

- addon prefs
  - sort individual tool prefs into per-tool sub panels
  - disable `avoid_append_reuse_import_method` setting
    - you are smart enough to disable _Append Reuse_, when you notice your inset meshes are linked :)
      - which is also very obvious now too due to the new button gizmo
- keymaps
  - expose native `view3d.cursor3d` keymap
    - and indicate potential conflicts with PointCursor (instant) `SHIFT + RMB` and TransformCursor `CTRL + RMB` keymaps
    - personally I prefer using `ALT + RMB` for the native tool, but now you can adjust either to your liking, or disable what you don't need
  - disable `ALT + SCROLL` cursor history entry change keymap by default
    - too often it triggers accidentally causing major disorientation
      - you can always pick a cursor history entry from the sidebar anyway, or by drawing them all in the 3D view

### internals

- refactor
  - completely rewrite and optimize and prettify (almost) all gizmo internals
  - completely rewrite and optimize and prettify all statusbar info
    - stop showing boolean props as "Something: False", instead shorten it and dim the entire entry if prop is False
    - support 4.3's extra-wide key icons
    - use new `MMB_SCROLL` icons in 4.3
  - completely rewrite and optimize how object wires are fetched and drawn
  - rework object visibility tooling
  - rework HUD drawing
  - rework scene recasting
  - create generic split boolean setup, used by HyperCut, AddObjectAtCursor and Boolean tools
  - mouse tracking and scrolling internals
    - support Apple Magic Mouse (I hope, please confirm)
    - support scrolling using UP and DOWN keys as well as PLUS and MINUS keys

- mod sorting
  - remove \* and \*\* sorting
    - all we need is + and -
  - support sorting of pinned mods (so at the end accordingly)

- asset dropping
  - simplify internals
  - fix Windows-only asset path issues introduced around Blender 4.0

- fix issues when changing workspace while some modal tools are active
  - add early CANCEL for ops returning PASS_THROUGH in case area changes due to workspace change

## 0.9.17

> 2024-05-21

- add Hyper Arrays (in Blender 4.1)
  - geo node based custom array mods for fully editable linear and radial arrays
    - NOTE: earlier Blender builds still use the legacy arrays using the array mod
    - like legacy radial arrays, radial **hyper** arrays still use an empty
      - but it's now used to determine the array origin and axis, instead of the first instance
        - this allows you to modify the radial array radius and axis effortlessly just by manipulating the relationship between empty and array object
        - further more, for multi-object radial **hyper** arrays the empty is now also shared among the objects/mods
  - set them up - just like before - using the TransformCursor tool, invoked while holding down `CTRL` when moving, dragging or rotating the main HC gizmo
  - edit **hyper** arrays using the new AdjustArray tool, invoked from the new Array object gizmo
    - or like any other geo nodes mod, from the native modifier panel
    - multi-object **hyper** arrays are linked together internally, and can be adjusted as one, IF you use the AdjustArray tool, toggle via `R` key
    - with mutiple hyper arrays present in a stack, support selecting a specific one to adjust via `CTRL + SCROLL`
    - draw elaborate preview coords for all of the different setup variations
    - support `S` and `SHIFT + S` finish to select radial array empty
    - adjust linear distance or radial angle by holding `T` key

- TransformCursor tool
  - in Blender 4.1 support setting up centered **hyper** arrays using the `C` key
  - make new custom PROJECTED_BOUNDS center method the default for face snapping
  - when drag snapping in EDIT_MESH mode in Blender 4.1, avoid temporarily disabling Auto Smooth mod if present
    - otherwise the mesh would appear completely smooth shaded (across all hard edges)
  - draw distance line for linear arrays, including a variation of it for centered hyper arrays
  - fix `CTRL + LMB DRAG` setup for linear arrays, which never worked correctly

- HyperBevel tool
  - support concave HyperBevels
    - automatically determine convexity based on first edge in sequence
    - for convance bevels, avoid overshooting the ends
      - and do a boolean UNION instead of a DIFFERENCE boolean
    - NOTE: may need additional manual adjustment of the cap faces
      - the MatchSurface tool is extremely useful here
  - when adding a weld mod (using `ALT`), add one in ALL instead of CONNECTED mode

- HyperCut tool
  - when finishing with `SPACE` hide the cutter(s), like is done in AddObjectAtCursor tool
  - for `SPLIT` cuts and when finishgni with `LMB` make the active's duplicate active, not the original active
    - this is because the split-off duplicate is likely the one, that you want to further edit/move/adjust the gap for, etc

- HyperCut, HyperBevel, PickObjectTree, PickHyperBevel tools
  - support finishing/switching into HyperMod via `TAB` key

- HyperMod tool
  - add new `ALT + W` keymapping to invoke in PICK mode
  - add new `ALT + SHIFT + W` keymapping to invoke in ADD mode
  - simplify ADD and PICK mode differences in statusbar, and only allow mod setting changes in PICK mode
  - support modal adjustment by holding `T` key of:
    - Weld threshold
    - Shell thickness
    - Displace strength
    - Auto Smooth angle
    - SubD levels and render levels
  - support switching into BevelEdge, AdjustShell, AdjustDisplace and new AdjustArray tools using `TAB` for specialized mod adjustments
  - for HyperBevels:
    - switch into EditHyperBevel tool, instead of PickHyperBevel (previously) using `TAB`
    - switch into ExtendHyperBevel tool using `ALT + E` (was possible before but not mentioned in statusbar)
  - for regular booleans also support finishing into PickObjectTree tool using `TAB`
  - in ADD mode add ability to add preceding double subd mods before a solidify mod using a second `S` key press
  - support applying (enabled) mods using `CTRL + A`
    - very useful also for applying only a part of the mod stack, when used in combination with `SHIFT + D`, which toggles mods from the current mod to the end of the stack
    - also automatically re-invoke HyperMod, when there are hidden mods, after you applied the enabled ones
  - support `SHIFT + S` to select mod objects without loosing initial object selection
    - great for radial array empty selection to move/scale/rotate the entire thing
    - NOTE: this is different from `SHIFT + S` in PickObjectTree too, which it will keep the tool running and allow for additive, sequential mod object selections
  - for SUBSURF mods, draw levels, render levels and subdivision algo in HUD
  - draw Radial Array and Radial Hyper Array empties and Mirror empties/objects, and support selecting them using `S` key and focusing on them using `F` key
  - draw EdgeBevel vgroup edges, similar to how boolean cutters are drawn
  - indicate invalid Edge Bevels
    - Edge Bevels are invalid if their vertex group does not create a single edge (anymore)

- PickObjectTree tool
  - use new `ALT + Q` keymapping
    - this frees `ALT + S` for the Blender native object scale reset again
  - support selecting radial hyper array empty using `S` or `SHIFT + S` keys
  - ensure you include wire mod objects in object tree, even those that are parented to another object
    - these were previously filtered out as part of a flawed attempt to exclude wire children of mirror mod objects
  - replace "alt. mod parent" terminology with "alt. mod host" instead
    - change keymap toggling their visibility/selectability from `P` to `H` accordingly
  - support finding mod objects referenced by any and all geo node mods

- AdjustShell tool
  - set the mod's `show_on_cage` prop based on the offset value
    - inwards (-1 offset): disable it, which is ideal, as she selection is very obvious then
    - centered and outwards: enable it, as otherwise the selection will be hidden and it would be hard to tell what's selected
    - unfortunately that also draws the faces that are result of the shelling
    - also with preceding subds it draws additional face dots as well

- AddObjectAtCursor tool
  - prevent toggling boolean for objects without a boolean parent present (empty scene)
  - also add simple range check and use it to disable the boolean mod if out of range
    - then when finishing, also remove any boolean mod, that was added again, IF the operand object is still out of range
  - remove "invalid" auto smooth mods created sometimes Blender when pasting or appending objects from earlier Blender versions
    - the terminal complains about them, and they lack the "Angel" or "Ignore Sharps" input on the geo node group
  - ensure scale is always applied when creating a unit cube or cylinder

- HideWireObjects tool
  - on _Windows_ use `SHIFT + ESC` keymapping now
  - avoid hiding empties set to IMAGE mode
  - support making arrayed and mirrored object active and selected, when array- or mirror-empty is selected, while HideWireObjects is invoked and said empties are hidden
- RemoveUnusedBoolean tool
  - add new `ALT + X` keymapping

- ApplyAll tool
  - unhide and deselect the mesh
    - otherwise applied union hyper bevels will have their cap faces still hidden
  - fix bl_idname in registration.py, causing the Screencast in MACHIN3tools to not show the HC prefix
  - remove unused edge bevel vgroups

- CastCursor tool
  - when cursor is not on screen pass the `SHIFT + C` keymap through to Blender
    - this way you can actually use the MACHIN3tools Collections pie, without leaving the HC tool

- Push Face tool
  - use Center Origin option by default
    - but prevent changing origin, when MIRROR (across object's origin) or (legacy) radial ARRAY is present, because changing the origin would (most likely) produce undesired results

- ChangeBackup tool
  - when recalling backup, default to removing the active and make hiding it optional, instead of the reverse

- DuplicateObject tool
  - avoid objects not in the view_layer (like decal backups, or stash objects) contributing to the object tree or mod dict
    - this happened towards the end of the recent Keycaps Process video

- CreaseEdge tool
  - prevent setting negative crease values

- AdjustCylinder tool
  - set geo gizmo edit mode to EDIT or SCALE, if the limit has been crossed in either direction due to the side count adjustment

- MatchSurface tool
  - if object has no modifiers, expose `R` key to toggle redundant (potential) shared edge removal
  - fix exception when aligning to face on active and active hosts modifiers

- CurveSurface tool
  - prevent exception when used on non-manifold geo, such as a lose face

- Toggle Gizmos tool
  - ensure the HUD elements and HC gizmos are drawn when toggling the main HC gizmo using `ESC`
    - otherwise you could get stuck in a state where the gizmos stay hidden, if you cancel TransformCursor's pass through to the transform or duplicate macros (SHIFT or ALT key invoke)

- GeoGizmoSetup tool
  - support edit mode invocation from MESHmachine, which now runs it after Fuse, Refuse, Unfuse, Unchamfer and Unbevel

- Object Gizmos
  - increase view border gap to 200 and take UI scaling into account as well

- Geometry Gizmos
  - fix geometry face gizmo placement on some faces, due to flaw in native `face.calc_center_bounds` method
    - introduce and use new custom PROJECTED_BOUNDS face center method
  - fix face and scale gizmos getting stuck being hidden, when finishing HyperCut in depth limit mode
  - fix exception after deleting the only or last face of a mesh

- Hyper Bevel Gizmos (Pick HyperBevel tool)
  - draw disabled HyperBevels with lower alpha

- mod sorting
  - support sorting new hyper arrays (to the end)
  - support CURVE mods, and sort them at the very end (after MIRROR and ARRAY)
  - remove "invalid" auto smooth mods created sometimes Blender when pasting or appending objects from earlier Blender versions
    - the terminal complains about them, and they lack the "Angle" or "Ignore Sharps" input on the geo node group

- rework 3D view sidebar, addon prefs, settings panel (HC gizmo) and help panel (tool header)
  - make use of new panel fold layouts in Blender 4.1 tointroduce panels and sub-panels for better grouping of related settings and info
    - also introduce legacy fallback approach that mirrors this look and behavior in earlier Blender versions
  - improve display of keymaps and support having them open prmanently (and only them) in the 3D view sidebar

- addon prefs
  - introduce tabs
    - Settings - support disabling HyperMod gizmo - with it being keymapped now, the gizmo becomes optional - support disabling reflect gizmo (MESHmachine Symmetrize and/or MACHNI3tools Mirror) as well
    - Keymaps
      - tighten how individual keymap items are drawn
      - add ResetKeymaps tool and expose it when ever keymaps are changed or removed by the user
        - draw it at the bottom the bottom of the keymaps tab

## 0.9.16

> 2024-04-01

- Blender 4.1 support

- add Bevel Profile example assets
  - support dropping them on HC's 'Edge Bevel' mods
    - drop them directly on the mesh, in proximity of an edge carrying an 'Edge Bevel' mod
  - support dropping them on HC's Hyper Bevels
    - need to be in PickHyperBevel mode, and drop them on the HyperBevel gizmos
  - NOTE: to drop them on WIRE objects, you have to be in WIRE shading mode too
    - as otherwise Blender won't snap on the objects

- add new thumbnails for Curve profile example assets

- BevelEdge and EditHyperBevel tools
  - indicate if a CUSTOMPROFILE is present, when in SUPERELLIPSE mode
  - support toggling from SUPERELLIPSE to CUSTOMPROFILE (if present) using `B` key
  - if CUSTOMPROFILE is chosen
    - visualize bevel profile
    - support flipping and flopping it using `F` and `V` keys
  - support canceling profile drops

- Edge Bevel tool
  - refactor
  - support re-sorting mod (incl. on instances) by holding down `ALT`, just like in HyperMod tool
    - unlike in HyperMod only sort among other `Edge Bevel` mods though
  - support additively assigning new edges to exsiting Edge Bevel mod
    - including re-assigning edges of other Edge Bevel's
  - support dropping profiles on instanced Edge Bevels
  - fully support percent bevels, including special case _locked_ FULL 100% percent bevels
    - cycle through OFFSET, PERCENT and FULL width modes using `Q` key
    - NOTE: converting from PERCENT to OFFSET or back is tricky, and only realy works on unit cubes
      - PERCENT bevels are inherently based on local topological conditions, which I won't take into account
  - support MESH beveling on top of MOD bevel (clearing the MOD bevel)
  - run validation/cleanup pass at the end, not the beginning
    1. check if Edge Bevel vgroups are referenced by any verts, and if not remove
    2. check if Edge Bevel mods (including on instances!) point to an Edge Bevel vgroup, and if not remove
    3. check if Edge Bevel vgroups are in use by Edge Bevel mods (including on instances!) and if not remove
    - draw fading message when unused vgroups or mods are removed after finishing
  - use MITER_ARC
  - flesh out HUD some more
  - fix edge gizmo creation on cylinders when doing MESH bevel

- HyperBevel tool
  - flesh out the first selection stage of the HUD some more
  - when redoing a HyperBevel (using `SPACE` key in selection stage) support doing it with a CUSTOMPROFILE (set/edited in EditHyperBevel tool or after dropping it)

- EditHyperBevel tool
  - support cycling `use_self` and `use_hole_tolerant` boolean mod props
    - similar to HyperMod tool, using `E` key, except here it's always EXACT, never FAST booleans
  - properly restore initial states when canceling

- Cast Cursor tool
  - support center casting via `C` key
    - cast half the target distance
    - great to position the cursor in the middle of an object or between two objects
  - also accidentally shooting the cursor into another galaxy
    - was a result of float imprecision, now there is a cutoff distance of 100000m, or 10km

- PushFace tool
  - support Extrude tool quick access via `CTRL` mod key
  - support nav passthrough in interactive mode
  - change HUD title from Move and Slide to Push Move and Push Slide
    - this is to differentiate it from the Move face tool

- PickObjectTree tool
  - fix issue where some empty crosses (for mirror or rotational arrays for instance) aren't drawn
  - for mirror and array mods don't use the evaluated mesh to determine the gizmo location
  - support finishing op with `LMB` when no gizmo is highlighted
  - be super strict about what keymap events are allowed to pass through, avoiding unnecessary object selections or operator invocations
  - improve 2d coordinate update after using _Focus using_ `F` or `ALT + F`

- PickHyperBevel tool
  - delay bevel removal, by first marking them, and only actually remove when finishing the op
  - draw gizmos in red, when HyperBevel is marked for removal
  - remove preceding Weld modes too, if both are linked together though their prefix
  - flesh out HUD and statusbar
  - support toggling HyperBevel using `D` key
  - support adjusting segment count directly by hovering on gizmo + scrolling, without having to invoke EditHyperBevel tool via `LMB`
    - temporarily activate wireframe, if you do so to better evaluate what's happening
  - support finishing op with `LMB` when no gizmo is highlighted
  - be super strict about what keymap events are allowed to pass through, avoiding unnecessary object selections or operator invocations
  - properly restore initial states when canceling

- RemoveUnusedBoolean tool and its GizmoGroup
  - bring everything up to date (mirroring the improvements made in PickObjectTree tool)
    - support _gizmo hovering_ by increasing size of gizmos and HUD elements
    - when highlighting an element, hide all others, but draw dots in their place, just like when doing navigation passthrough
      - draw dots in red or white, depending on remove/keep mode
    - draw highlighted wire twice - with and without xray
  - support finishing op with `LMB` when no gizmo is highlighted
  - be super strict about what keymap events are allowed to pass through, avoiding unnecessary object selections or operator invocations
    - this allows for dropping the previous use of `hide_select` of all other visible objects
      - which was such an awkward way to avoid with accidental passthrough selection events
  - support for keyboard based toggling and focusing
    - use `X` to toggle remove/keep state
    - use `D` to toggle `mod.show_viewport`
    - use `F` and `ALT + F` to focus or place the view
  - flesh out statusbar
  - improve unused boolean check by also taking dimensions change into account
  - improve 2d coordinate update after using Focus using `F` or `ALT + F`
  - always draw wires of mods/objects set to _keep_
    - this visually indicates they are important and keeping them visible indicates they will remain so and not be removed

- AddObjectAtCursor tool
  - add automatic but optional subset mirroring base on presence of Mirror mods on the active (boolean parent) object
    - only mirror non-wire, non-hook-handle objects
    - toggle via `M` key
  - when enabling and disabling boolean in the modal, ensure the mod is removed again when finishing with it disabled
  - when hiding booleans by finishing via `SPACE`, make the "boolean parent" active and selected
    - except when adding a hook inset, then select the hook object, no matter how you finish the op
  - deal with Blender auto-added Auto Smooth mods when adding an Asset
    - turns out it is fucked up after appending, and doesn't even have an _Input_1_ prop, so just remove the mod in such cases

- Add Pipe tool
  - enable caps by default
  - increase default bevel resolution from 4 to 12

- AdjustPipe tool
  - redo HUD completely
  - replace previous PROFILE mode with DIAMOND and SQUARE modes
    - so there are 4 now: ROUND, DIAMOND, SQUARE and OBJECT
      - for OBJECT to be available you have to have dropped one or more profile curve objects on the pipe
    - cycle through them using `B` keys
  - only expose pipe resolution for ROUND mode
  - support toggling _Fill Caps_ via `C` key
  - in Blender 4.1, if the pipe is smooth shaded (`S` key), allow toggling Auto Smooth via `A` key
  - add Smooth / Auto Smooth indicators in HUD
  - properly restore initial states when canceling
  - adjust mouse sensitivity

- HyperMod tool
  - indicate if EdgeBevel mod has CUSTOMPROFILE
  - by default avoid toggling Auto Smooth mod when toggling all mods via `A` key

- FocusProximity tool
  - with auto_clip_start disabled, use the initial clip start value, not 0.05
  - remember `adjust_clip_start` prop

- ExtractFace tool
  - remember `fill_angle` prop, and lower the default from 60 to 20

- HyperBend tool
  - support finishing op with `LMB` when no gizmo is highlighted
  - be super strict about what keymap events are allowed to pass through, avoiding unnecessary object selections or operator invocations

- DuplicateBoolean tool
  - only let HC takeover the boolean duplication, when HC tool is active

- FlattenFace tool
  - fix unpredictable results, depending on view

- LoopCut tool
  - fix exception when ALT redoing

- CreateAsset tool
  - fix exception when trying to change existing asset

- Geometry Gizmos
  - refactor and improve when and how they are updated or re-created
  - ToggleGizmoDataLayerPreview and ToggleGizmo tools (edit mode HC context menu, or in MACHIN3tools Modes pie)
    - add operator descriptions
    - change preview colors from red and orange, to green and blue
  - for WIRE objects, don't dim the backside gizmos and avoid toggling out of XRAY mode
  - fix gizmo size/direction issue with objects that are scaled negatively (on one or three axes)
  - avoid showing for multi object selections

- Object Gizmos
  - refactor and improve when and how they are updated or re-created
  - fix exception when deleting CURVE object and selecting MESH object afterwards
  - avoid showing for multi object selections

- addon preferences
  - add custom updater
  - add option to avoid toggling Auto Smooth mod in HyperMod tool
  - expose global geometry gizmo scale pref
  - make debug addon registration output in system console optional

- modifier sorting
  - in Blender 4.1 support Auto Smooth sorting
    - towards the end of the stack, but before Mirror and Array mods

- update fading info/warning label drawing everywhere
- add _grip header bar_ to Object, GeoGizmo and HyperCursor Setting panels

## 0.9.15

> 2024-02-18

- support Blender 4

- add MoveFace tool
  - NOTE: different from PushFace, MoveFace moves in the face's plane
  - support opposite face selection via raycast, by invoking the tool with `SHIFT` mod key
  - support moving hyper selected faces too
  - support numeric input in modal
  - support nav passthrough
  - support ALT repeat
    - but note, what is X or Y direction for one face, may be a different for another face
  - support redo panel

- HyperCut tool
  - flesh out HUD some more and make the 2 stage proces more clear:
    1. draw plane selection (bbox, face, cursor)
    2. drag out the hyper cut direction
  - support snapping on other objects (non-active, non-wire) objects using `SHIFT + CTRL`
  - draw additional snapping lines in VIEW3D
    - pretty cool for cases whwre snapper coords are not in the drawing plane already
  - draw depth indicators as fading vectors
  - draw the side indictor even when splitting now
    - this indicates where the cutter object is created, so is useful info
  - only draw HUD and VIEW3D elements in the area (=the 3d view) the tool was invoked in
  - support limiting cutting depth by holding `D` key
    - changes the view and lets you scroll to adjust the depth
  - support limiting cutting width by toggling `W` key
    - scroll to adjust the width
  - fix issues naming the two mods for split booleans
  - for split cuts, add "(Split Difference)" and "(Split Intersect)" to mod names
    - instead of just ("Difference") and "(Intersect)" as before
  - fully support HOps smart objects
    - check if mesh bbox is infinitely small, and if so fetch the evaluated bbox instead for drawing on
    - avoid mod sorting for objects that aren't ishyper
  - support lazy splitting using `Q` (in split mode)
    - creates a non-manifold plane object cutter, with a shell (solidify) mod

- PushEdge tool
  - indicate mouse movement direction in HUD
  - fix issues with scaled objects
  - support numeric input
  - supprot shift/ctrl precision adjustment in interacitve mode
  - support nav passthrough without affecting the push amount
  - support ALT repeat
    - but note, what is X or Y direction for one face, may be a different for another face
  - support redo panel

- ExtrudeFace tool
  - rewrite completely
  - support opposite face selection via raycast, by invoking the tool with `SHIFT` mod key
  - support extruding multiple hyper selected faces at once
    - with multiple connected faces present
  - support toggling individual extrude
  - support cycling extruson modes Selected, Avergated and Vert
  - support nav passthrough without affecting the extrusion amount
  - deal with vertex groups, bevel weights, creases, seams and sharps on the extuded geo
    - it's seems to be wise to clear them on the "outer geo", wich is essentially the original geo
  - make it work on non-manifold geo, such as simple planes or circles

- InsetFace tool
  - rewrite completely
  - support opposite face selection via raycast, by invoking the tool with `SHIFT` mod key
  - support inset and outset depending on the direction of the mouse movement
    - insetting is blue, outsetting is red
  - support insetting multiple hyper selected faces at once
    - support toggling individual inset with multiple connected faces present
  - support toggling even and edge rail using `E` and `R` keys
  - support toggling Auto Outset using `A` key
    - with it disabled you can inset outwards, growing the face instead of shrinking it
    - with it enabled you _inset_ into the neighboring faces, shrinking them
  - deal with vertex groups, bevel weights, creases, seams and sharps on the inset geo
    - it seems to be wise to clear them on the "inner geo" when insetting and on the outer geo when outsetting
  - support insetting on non-manifold geo (such as a single face object)
  - support nav passthrough without affecting the inset amount
  - support ALT repeat
    - but note, what is X or Y direction for one face, may be a different for another face
  - support redo panel

- ScaleFace tool
  - rewrite comepltely and use manual scaling instad of bmesh op
    - turns out it's twice as fast to do it manually too
  - support opposite face selection via raycast, by invoking the tool with `SHIFT` mod key
  - unlike in the previous version, scale by moving the mouse in the face plane, not along its normal
    - the diection is determined by the initial mouse position in relationg to the face origin
    - a line is drawn to visualize this
    - this allows flawless scaling in positive and negative directions, even when looking at the face head on, which is more natural than ensuring you look on it in a 3/4 view
  - support numeric input in modal
    - you can now simply toggle negation using `-`, even if an amount is already typed out
  - toggle merge instead of scale via `ÀLT` key
  - initiate X, Y or XY axes based on mouse positon on face ring gizmo
    - but only for CUBE objects
  - support nav passthrough without affecting the scale amount
  - support ALT repeat
    - but note, what is X or Y direction for one face, may be a different for another face
  - support redo panel

- PushFace tool
  - when sliding, fall back to use the vert normal when no slide edge is found
  - when object has mods, temporarily enable show_wire
  - test very simple unit support, and only in the redo panel for now

- TransformCursor
  - refactor and simplify
  - flesh out and improve HUD some more
  - support numeric input
    - when pressing BACKSPACE leave only 4 post comma digits standing
    - with ALT + BACKSPACE you can remove only the last one
    - when the input is marked, you can now press - to negate, which won't clear the entire string anymore
  - make angle snapping immediate when pressing CTRL
  - draw additional lines when sliding on snapped face or edge
  - support nav passthrough
    - execept when rotating in interactive mode (so do support it in numeric input mode)
  - properly indicate initial cursor origin when dragging via `CTRL - RMB` or from MACHIN3tools cursor pie
  - show cursor's absolute coords in HUD, toggle via `A` key

- AddObjectAtCursor tool
  - overhaul HUD and statusbar
  - in HUD also indicate boolean object if present
  - don't apply cast and subd mods for assets that are brought in with the tool
  - support numeric input
  - at the begining warp mouse into cursor's origin
    - this allows us to actually draw out the object size from the the placement origin
  - support switching a cube to a plane and a cylinder to a circle using `C` key
    - and support X and Y axis alignment planes (not possible (or necessary) for cubes)
  - support turning Cylinder/Circle into Half/Semi Cylinder/Circle unsing `V` or `H` keys
    - NOTE: for rounded half cylinders, the bevel width will be based on segment count to avoid overshoots
  - support toggling cylinder side preset mode via `Q` key to directly adjust them
  - fully support redoing
  - support duplicate catalog entries in Blender's catalog definition files
  - fix execption in prettified asset path when non-object asset was selected in asset browser
  - fix "floating" curve profiles in surface mode
  - fix exception when adding an asset, while nothing is selected in the asset browser, and display a fading warning message
  - fix exception when selected asset in asset browser no longer exists on disk

- AdjustCylinder tool
  - tweak HUD a little
  - support adjusting circles
  - change the keymap from `A` to `Q` for switching segment preset mode
  - support numeric input
  - flesh out redo panel a little more

- AdjustShell tool
  - properly init solidify mod's thickness based on min bbox dimensions, but ignoreing 0 dims
  - support toggling high quality normals using N, and by default enable it
  - support offset cycling between -1, 0 and 1 (inwards, centered, outwards)
  - remove Start/End sorting
    - with the introduction of HyperMod and having the ability to precisely place a mod anywhere in the stack and make it stick using the - and + prefixes, this is obsolete now
  - add precision indicators in HUD and statusbar
  - add high quality normals to statusbar
  - fix rare view orientation/location dependent precision issues

- AdjustDisplace tool
  - indicate remote object name in HUD, if present
  - add precision indicators in HUD and statusbar
  - fix rare view orientation/location dependent precision issues

- MatchSurface tool
  - preview hitface by drawing it in VIEW3D
  - prevent "self-matching" index face, and give feedback in the HUD accordingly
  - support matching face normal only using `ALT` key
    - this avoids moving the face
  - add statusbar info

- CurveSurface tool
  - flesh out the HUD a little more
    - give Amount/Depth, Subdivisions and Pinch each a separate line, instead of cramming them all into one line without indication what each number is
  - also, be very selective about what keys are allowed to pass through for selection: only MOUSEMOVE and LEFTMOUSE is truly required

- FocusProximity tool
  - refactor
  - flesh out HUD
  - support precision mod keys
  - ensure clip_start is 0.05 if proximity is 1
  - support NDOF navigation passthrough
  - draw cursor axes, when cursor is not shown, or when MACHIN3tools doesn't draw the axes already

- CreateAsset tool
  - fix exeption for multi-obj seletions without a single root object

- AdjustCurveSurfacePoint tool
  - fix issue of movement plane not being created properly anymore, as the view_origin was accidentally used for view_dir

- Blendulate tool
  - show gizmo even for NURBS curves, which are supported since 0.9.14 (like in CURVEmachine 1.2)
  - adjust zoom factor a little to make adjustment a bit more precise by default

- SnapRotate tool
  - prevent exection when object or cursor is positioned out of the field of view
  - draw fading warning about placing the object/cursor in the field of view

- PointCursor tool
  - mention mouse move to pick face/edge in statusbar
  - fix exception when aligning Y axis via `ALT`, but not hitting anything with the raycast

- CastCursor tool
  - replace popup message with fading label, if cursor is located outside of the view

- BevelEdge tool
  - fix issue where instanced objects with bevel mods wern't mod sorted

- CreaseEdge tool
  - emphasize selected edges and their crease amount comparerd to unselected creased edges

- AddPipe tool
  - improve and simplify how currently enabled gizmos are temporarliy disabled and then restored again at the end

- AdjustPipeArc tool
  - flesh out HUD to show both Radius and Segments at the same time

- AdjustPipe tool
  - fix rare view orientation/location dependent precision issues

- SnapRotate tool
  - hide and restore gizmos IF and object is rotated

- PushFace tool
  - draw mouse guide line

- HideWireObjects tool
  - avoid hiding empties using and instance collection

- PickObjectTree tool
  - reverse colors for 1st degree an 2nd (and lower) degree children: green for 1st, yellow for the others
  - increasinly lower the alpha for lower children, the deeper it goes

- DuplicateBoolean tool
  - fix exeption in Blender 4 due to removal of tool_settings.use_snap_project

- AddObject pie
  - indicate when no asset browser is on the workspace
  - indicate when no OBJECT asset is selected

- HyperCursor HUD
  - only show the cursor history 'current / count' when the history buttons are shown too
    - or when positioned in a stored cursor history location right now
  - also, when in a stored history location right now, draw the current index in green, matching the green circle in the center and the Auto label

- Geometry Gizmos
  - set face ring and arrow gizmo sizes based on face area
    - actually tweened (adustable) between mesh dimension factor and face dimension factor
    - provides better gizmo sizes for meshes with varying face sizes
  - set face gizmo location based on calc_center_bounds(), not calc_center_median()
  - expose edge_tickness and face_tween values to object's gizmo menu
  - lower edge thickness to 0.7 (adjustable)
  - increase face ring gizmos a little when highlighting them

- sidebar panel
  - expose clip_start next to focus_proximity in the sidebar panel
    - the reset op right next to them affects both

- addon prefs
  - add option to disable mod buttons in Blender's modifier panel

- add precision indication in HUDs of
  - SnapRotate, SlideEdge, CreaseEdge

- ensure HUDs and gizmos are drawn in active view only
  - AddObjectAtCursor, AddPipe, AdjustCylinder, SnapRotate, AdjustPipeArc
  - PointCursor, CastCursor
  - PushEdge, LoopCut, CreaseEdge
  - PushFace, ExtractFace, CurveSurface, AdjustCurveSurfacePoint, MatchSurface
  - HyperBevel, HyperMod, HyperBend, EditHyperBevel, PickHyperBevel
  - Blendulate

- completely redo (mouse) cursor warping, region-wrapping, and other mouse position related internal tooling
  - TransformCursor, PointCursor, FocusProximity, PickObjectTree, AddObjectAtCursor
  - BevelEdge, SlideEdge, CreaseEdge, LoopCut
  - PushFace, CurveSurface, AdjustCurveSurfacePoint
  - ScaleMesh
  - AddPope, AdjustPipe, AdjustPipeArc, AdjustShell, AdjustDisplace, AdjustCylinder
  - EditHyperBevel, ExtendHyperBevel, Blendulate, SnapRotate, MatchSurface
  - HyperCut, HyperBevel, HyperMod, HyperBend, ExtendHyperBevel

- delay all handler execution using timer as is done in MACHIN3tools, MESHmachine, DECALmachine and CURVEmachine now
  - should hopefully prevent any potential issues with other addons due to recursive depsgraph updates
  - also it looks like the asset dropping with HyperCursor taking over right after now works without any issues even with other windows (preferences, 3d view) open
  - do MACHIN3tools-style post-asset-drop-cleanup, that skips if MM and DM have that capability on their own (with the next updates)

- change HyperCursor keymap in Toolbar from H to C
  - easier to reach from the left side of the keyboard, and the native Cursor tool already uses spacebar, while C is free

- fix exception when mod sorting objects without mods
- fix exception when dropping (hyper) asset into scene, while active object was None due to previously deleted object
- fix potential exceptions in operator search menu

## --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
