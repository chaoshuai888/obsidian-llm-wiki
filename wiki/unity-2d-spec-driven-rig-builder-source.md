# Unity 2D Spec-Driven Rig Builder 源码快照

Status: wiki
Last verified: 2026-06-12
Sources embedded: complete

Summary:
本页内嵌 Spec-Driven Rig Builder 的完整源码快照，避免只记录本地路径导致后续项目移动后无法追溯。源码快照来自 2026-06-12 的 NovaBot 通用化实现。

验证结果：

```text
EditMode tests: 13/13 passed
NovaBot_SpecIdle: curves=18, missing=0
NovaBot_SpecRun: curves=28, missing=0
Console errors: 0
```

## SpecDrivenRigBuilder.cs

```csharp
using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEditor.Animations;
using UnityEngine;

namespace NovaBot.Editor
{
    public static class SpecDrivenRigBuilder
    {
        private const float DefaultPixelsPerUnit = 100f;

        public sealed class SpecSet
        {
            public string folder;
            public BoneSpec boneSpec = new BoneSpec();
            public LayerSpec layerSpec = new LayerSpec();
            public SortingSpec sortingSpec = new SortingSpec();
            public MotionSpec motionSpec = new MotionSpec();
        }

        public sealed class BoneSpec
        {
            public string character = "Character";
            public string pose = "FrontAPose";
            public CanvasSpec canvas = new CanvasSpec();
            public OutputSpec output = new OutputSpec();
            public Dictionary<string, BoneEntry> bones = new Dictionary<string, BoneEntry>(StringComparer.OrdinalIgnoreCase);
        }

        public sealed class CanvasSpec
        {
            public int width = 2048;
            public int height = 2048;
            public string origin = "top_left_pixels";
        }

        public sealed class OutputSpec
        {
            public string prefab_path;
            public string clip_folder;
            public string controller_path;
        }

        public sealed class BoneEntry
        {
            public string parent;
            public float[] head_px = Array.Empty<float>();
            public float[] tail_px = Array.Empty<float>();
        }

        public sealed class LayerSpec
        {
            public string psb_path;
            public List<LayerEntry> layers = new List<LayerEntry>();
        }

        public sealed class LayerEntry
        {
            public string name;
            public string bone;
            public bool visible = true;
        }

        public sealed class SortingSpec
        {
            public List<SortingEntry> orders = new List<SortingEntry>();
        }

        public sealed class SortingEntry
        {
            public string layer;
            public int order;
        }

        public sealed class MotionSpec
        {
            public List<MotionClipSpec> clips = new List<MotionClipSpec>();
        }

        public sealed class MotionClipSpec
        {
            public string name;
            public string path;
            public float fps = 24f;
            public float duration = 1f;
            public bool loop = true;
            public List<MotionTrackSpec> tracks = new List<MotionTrackSpec>();
        }

        public sealed class MotionTrackSpec
        {
            public string target;
            public string target_type = "bone";
            public string property;
            public List<Keyframe> keys = new List<Keyframe>();
        }

        public sealed class ValidationReport
        {
            public readonly List<string> missingLayers = new List<string>();
            public readonly List<string> missingBones = new List<string>();
            public readonly List<string> duplicateLayers = new List<string>();
            public readonly List<string> duplicateBones = new List<string>();
            public readonly List<string> sortingConflicts = new List<string>();
            public readonly List<string> motionBindingIssues = new List<string>();

            public bool HasIssues =>
                missingLayers.Count > 0 ||
                missingBones.Count > 0 ||
                duplicateLayers.Count > 0 ||
                duplicateBones.Count > 0 ||
                sortingConflicts.Count > 0 ||
                motionBindingIssues.Count > 0;
        }

        [MenuItem("Tools/AI Rig/Build From Selected Spec")]
        public static void BuildFromSelectedSpec()
        {
            var spec = LoadSelectedSpecSet();
            var availableLayers = FindAvailableSpriteLayerNames(spec).ToArray();
            var report = ValidateSpecSet(spec, availableLayers);
            var prefab = BuildRigPrefab(spec, report);
            LogReport("Build From Selected Spec", report, prefab != null ? AssetDatabase.GetAssetPath(prefab) : string.Empty);
        }

        [MenuItem("Tools/AI Rig/Generate Animation From Motion Spec")]
        public static void GenerateAnimationFromMotionSpec()
        {
            var spec = LoadSelectedSpecSet();
            var clips = GenerateAnimationClips(spec);
            LogReport("Generate Animation From Motion Spec", ValidateSpecSet(spec, FindAvailableSpriteLayerNames(spec)), string.Join(", ", clips.Select(AssetDatabase.GetAssetPath)));
        }

        [MenuItem("Tools/AI Rig/Validate Character Rig")]
        public static void ValidateCharacterRig()
        {
            var spec = LoadSelectedSpecSet();
            var report = ValidateSpecSet(spec, FindAvailableSpriteLayerNames(spec));
            LogReport("Validate Character Rig", report, string.Empty);
        }

        public static SpecSet LoadSpecSet(string folder)
        {
            return new SpecSet
            {
                folder = folder,
                boneSpec = LoadBoneSpec(FindRequiredSpecPath(folder, "bone_spec.json")),
                layerSpec = LoadLayerSpec(FindRequiredSpecPath(folder, "layer_spec.json")),
                sortingSpec = LoadSortingSpec(FindOptionalSpecPath(folder, "sorting_spec.json")),
                motionSpec = LoadMotionSpec(FindOptionalSpecPath(folder, "motion_spec.json"))
            };
        }

        public static ValidationReport ValidateSpecSet(SpecSet spec, IEnumerable<string> availableLayerNames)
        {
            var report = new ValidationReport();
            var availableLayers = new HashSet<string>(availableLayerNames ?? Enumerable.Empty<string>(), StringComparer.OrdinalIgnoreCase);
            var layerNames = spec.layerSpec.layers.Select(layer => layer.name).Where(name => !string.IsNullOrEmpty(name)).ToList();
            var layerSet = new HashSet<string>(layerNames, StringComparer.OrdinalIgnoreCase);

            AddDuplicates(layerNames, report.duplicateLayers);
            AddDuplicates(spec.boneSpec.bones.Keys, report.duplicateBones);

            foreach (var bone in spec.boneSpec.bones.Values)
            {
                if (!string.IsNullOrEmpty(bone.parent) && !spec.boneSpec.bones.ContainsKey(bone.parent))
                    AddUnique(report.missingBones, bone.parent);
            }

            foreach (var layer in spec.layerSpec.layers)
            {
                if (!string.IsNullOrEmpty(layer.bone) && !spec.boneSpec.bones.ContainsKey(layer.bone))
                    AddUnique(report.missingBones, layer.bone);
                if (availableLayers.Count > 0 && !availableLayers.Contains(layer.name))
                    AddUnique(report.missingLayers, layer.name);
            }

            foreach (var sorting in spec.sortingSpec.orders)
            {
                if (!layerSet.Contains(sorting.layer) && (availableLayers.Count == 0 || !availableLayers.Contains(sorting.layer)))
                    AddUnique(report.missingLayers, sorting.layer);
            }

            foreach (var group in spec.sortingSpec.orders.GroupBy(order => order.order))
            {
                var layers = group.Select(entry => entry.layer).Where(layer => !string.IsNullOrEmpty(layer)).Distinct(StringComparer.OrdinalIgnoreCase).ToArray();
                if (layers.Length > 1)
                    report.sortingConflicts.Add("order " + group.Key + ": " + string.Join(", ", layers));
            }

            foreach (var clip in spec.motionSpec.clips)
            {
                foreach (var track in clip.tracks)
                {
                    if (IsLayerTrack(track))
                    {
                        if (!layerSet.Contains(track.target))
                            AddUnique(report.missingLayers, track.target);
                    }
                    else if (!spec.boneSpec.bones.ContainsKey(track.target))
                    {
                        AddUnique(report.missingBones, track.target);
                    }
                }
            }

            return report;
        }

        public static Dictionary<string, Transform> CreateBoneHierarchy(GameObject rigRoot, BoneSpec boneSpec, float pixelsPerUnit)
        {
            var bones = new Dictionary<string, Transform>(StringComparer.OrdinalIgnoreCase);
            var positions = new Dictionary<string, Vector3>(StringComparer.OrdinalIgnoreCase);
            foreach (var boneName in TopologicalBoneNames(boneSpec))
            {
                var entry = boneSpec.bones[boneName];
                var go = new GameObject(boneName);
                var transform = go.transform;
                var worldPosition = CanvasPixelToLocal(ToVector2(entry.head_px), boneSpec.canvas, pixelsPerUnit);
                positions[boneName] = worldPosition;
                transform.SetParent(string.IsNullOrEmpty(entry.parent) ? rigRoot.transform : bones[entry.parent], false);
                transform.localPosition = string.IsNullOrEmpty(entry.parent) ? worldPosition : worldPosition - positions[entry.parent];
                transform.localRotation = Quaternion.identity;
                transform.localScale = Vector3.one;
                bones[boneName] = transform;
            }

            return bones;
        }

        public static GameObject BuildRigPrefab(SpecSet spec, ValidationReport report)
        {
            var psbPath = ResolveAssetPath(spec.folder, spec.layerSpec.psb_path) ?? FindFirstPsbPath(spec.folder);
            var source = !string.IsNullOrEmpty(psbPath) ? AssetDatabase.LoadAssetAtPath<GameObject>(psbPath) : Selection.activeGameObject;
            if (source == null)
                throw new InvalidOperationException("Could not find source PSB prefab from spec or selection.");

            var instance = PrefabUtility.InstantiatePrefab(source) as GameObject;
            if (instance == null)
                instance = UnityEngine.Object.Instantiate(source);
            PrefabUtility.UnpackPrefabInstance(instance, PrefabUnpackMode.Completely, InteractionMode.AutomatedAction);

            var rootName = string.IsNullOrEmpty(spec.boneSpec.character) ? "Rig" : spec.boneSpec.character + "_Rig";
            instance.name = rootName;
            var oldRoot = instance.transform.Find("root");
            if (oldRoot != null)
                UnityEngine.Object.DestroyImmediate(oldRoot.gameObject);

            var ppu = ReadPixelsPerUnit(psbPath, DefaultPixelsPerUnit);
            var bones = CreateBoneHierarchy(instance, spec.boneSpec, ppu);
            ApplyLayerParenting(instance, bones, spec, report);
            ApplySorting(instance, spec.sortingSpec);

            var prefabPath = ResolveAssetPath(spec.folder, spec.boneSpec.output.prefab_path);
            if (string.IsNullOrEmpty(prefabPath))
                prefabPath = "Assets/" + rootName + ".prefab";
            EnsureAssetFolder(Path.GetDirectoryName(prefabPath));
            var prefab = PrefabUtility.SaveAsPrefabAsset(instance, prefabPath);
            UnityEngine.Object.DestroyImmediate(instance);
            AssetDatabase.SaveAssets();
            return prefab;
        }

        public static List<AnimationClip> GenerateAnimationClips(SpecSet spec)
        {
            var clips = new List<AnimationClip>();
            var targetRoot = Selection.activeGameObject != null ? FindSpecRoot(Selection.activeGameObject) : FindSceneRoot(spec.boneSpec.character);
            var bonePathByName = BuildBonePathMap(targetRoot, spec.boneSpec);
            var controllerPath = ResolveAssetPath(spec.folder, spec.boneSpec.output.controller_path);
            AnimatorController controller = null;
            if (!string.IsNullOrEmpty(controllerPath))
            {
                EnsureAssetFolder(Path.GetDirectoryName(controllerPath));
                controller = AssetDatabase.LoadAssetAtPath<AnimatorController>(controllerPath) ?? AnimatorController.CreateAnimatorControllerAtPath(controllerPath);
            }

            foreach (var clipSpec in spec.motionSpec.clips)
            {
                var clip = new AnimationClip { frameRate = clipSpec.fps > 0f ? clipSpec.fps : 24f };
                foreach (var track in clipSpec.tracks)
                    AddTrackCurve(clip, track, bonePathByName, targetRoot);

                var settings = AnimationUtility.GetAnimationClipSettings(clip);
                settings.loopTime = clipSpec.loop;
                AnimationUtility.SetAnimationClipSettings(clip, settings);

                var clipPath = ResolveAssetPath(spec.folder, clipSpec.path);
                if (string.IsNullOrEmpty(clipPath))
                {
                    var folder = ResolveAssetPath(spec.folder, spec.boneSpec.output.clip_folder);
                    if (string.IsNullOrEmpty(folder))
                        folder = AssetDatabase.IsValidFolder("Assets/Generated") ? "Assets/Generated" : "Assets";
                    clipPath = folder.TrimEnd('/') + "/" + SanitizeAssetName(clipSpec.name) + ".anim";
                }
                EnsureAssetFolder(Path.GetDirectoryName(clipPath));
                SaveAnimationClip(clip, clipPath);
                var savedClip = AssetDatabase.LoadAssetAtPath<AnimationClip>(clipPath);
                clips.Add(savedClip);
                if (controller != null)
                    EnsureState(controller.layers[0].stateMachine, clipSpec.name, savedClip, new Vector3(240f, 80f + 80f * clips.Count, 0f));
            }

            if (controller != null)
                EditorUtility.SetDirty(controller);
            AssetDatabase.SaveAssets();
            return clips;
        }

        private static SpecSet LoadSelectedSpecSet()
        {
            var selectedPath = AssetDatabase.GetAssetPath(Selection.activeObject);
            if (string.IsNullOrEmpty(selectedPath) && Selection.activeGameObject != null)
                selectedPath = PrefabUtility.GetPrefabAssetPathOfNearestInstanceRoot(Selection.activeGameObject);
            var folder = AssetPathToFullPath(AssetDatabase.IsValidFolder(selectedPath) ? selectedPath : Path.GetDirectoryName(selectedPath));
            if (string.IsNullOrEmpty(folder) || !Directory.Exists(folder))
                throw new InvalidOperationException("Select a spec json, PSB, prefab, or folder inside a character spec directory.");
            return LoadSpecSet(folder);
        }

        private static BoneSpec LoadBoneSpec(string path)
        {
            var root = Json.Parse(File.ReadAllText(path)) as Dictionary<string, object>;
            var spec = new BoneSpec
            {
                character = StringValue(root, "character", "Character"),
                pose = StringValue(root, "pose", StringValue(root, "view", "FrontAPose")),
                canvas = ParseCanvas(ObjectValue(root, "canvas")),
                output = ParseOutput(ObjectValue(root, "output"))
            };

            var bones = ObjectValue(root, "bones");
            foreach (var pair in bones)
            {
                var bone = pair.Value as Dictionary<string, object>;
                spec.bones[pair.Key] = new BoneEntry
                {
                    parent = StringValue(bone, "parent", null),
                    head_px = FloatArray(bone, "head_px"),
                    tail_px = FloatArray(bone, "tail_px")
                };
            }

            return spec;
        }

        private static LayerSpec LoadLayerSpec(string path)
        {
            var root = Json.Parse(File.ReadAllText(path)) as Dictionary<string, object>;
            var spec = new LayerSpec { psb_path = StringValue(root, "psb_path", StringValue(ObjectValue(root, "source_files"), "layered_psb", null)) };
            foreach (var entry in ArrayValue(root, "layers").Concat(ArrayValue(root, "layers_back_to_front")))
            {
                var layer = entry as Dictionary<string, object>;
                var name = StringValue(layer, "name", null);
                if (string.IsNullOrEmpty(name))
                    continue;
                spec.layers.Add(new LayerEntry
                {
                    name = name,
                    bone = StringValue(layer, "bone", null),
                    visible = BoolValue(layer, "visible", true)
                });
            }
            return spec;
        }

        private static SortingSpec LoadSortingSpec(string path)
        {
            var spec = new SortingSpec();
            if (string.IsNullOrEmpty(path) || !File.Exists(path))
                return spec;
            var root = Json.Parse(File.ReadAllText(path)) as Dictionary<string, object>;
            foreach (var entry in ArrayValue(root, "orders"))
            {
                var order = entry as Dictionary<string, object>;
                spec.orders.Add(new SortingEntry { layer = StringValue(order, "layer", null), order = IntValue(order, "order", 0) });
            }
            return spec;
        }

        private static MotionSpec LoadMotionSpec(string path)
        {
            var spec = new MotionSpec();
            if (string.IsNullOrEmpty(path) || !File.Exists(path))
                return spec;
            var root = Json.Parse(File.ReadAllText(path)) as Dictionary<string, object>;
            foreach (var clipObject in ArrayValue(root, "clips"))
            {
                var clipMap = clipObject as Dictionary<string, object>;
                var clip = new MotionClipSpec
                {
                    name = StringValue(clipMap, "name", "Clip"),
                    path = StringValue(clipMap, "path", null),
                    fps = FloatValue(clipMap, "fps", 24f),
                    duration = FloatValue(clipMap, "duration", 1f),
                    loop = BoolValue(clipMap, "loop", true)
                };
                foreach (var trackObject in ArrayValue(clipMap, "tracks"))
                {
                    var trackMap = trackObject as Dictionary<string, object>;
                    var track = new MotionTrackSpec
                    {
                        target = StringValue(trackMap, "target", null),
                        target_type = StringValue(trackMap, "target_type", "bone"),
                        property = StringValue(trackMap, "property", null),
                        keys = ParseKeys(ArrayValue(trackMap, "keys"), clip.fps)
                    };
                    clip.tracks.Add(track);
                }
                spec.clips.Add(clip);
            }
            return spec;
        }

        private static void ApplyLayerParenting(GameObject root, Dictionary<string, Transform> bones, SpecSet spec, ValidationReport report)
        {
            var renderers = root.GetComponentsInChildren<SpriteRenderer>(true);
            foreach (var layer in spec.layerSpec.layers.Where(layer => layer.visible))
            {
                var renderer = renderers.FirstOrDefault(candidate => string.Equals(candidate.name, layer.name, StringComparison.OrdinalIgnoreCase) ||
                    (candidate.sprite != null && string.Equals(candidate.sprite.name, layer.name, StringComparison.OrdinalIgnoreCase)));
                if (renderer == null)
                {
                    AddUnique(report.missingLayers, layer.name);
                    continue;
                }
                if (!bones.TryGetValue(layer.bone, out var bone))
                {
                    AddUnique(report.missingBones, layer.bone);
                    continue;
                }
                renderer.transform.SetParent(bone, true);
            }
        }

        private static void ApplySorting(GameObject root, SortingSpec sortingSpec)
        {
            var renderers = root.GetComponentsInChildren<SpriteRenderer>(true);
            foreach (var sorting in sortingSpec.orders)
            {
                var renderer = renderers.FirstOrDefault(candidate => string.Equals(candidate.name, sorting.layer, StringComparison.OrdinalIgnoreCase) ||
                    (candidate.sprite != null && string.Equals(candidate.sprite.name, sorting.layer, StringComparison.OrdinalIgnoreCase)));
                if (renderer != null)
                    renderer.sortingOrder = sorting.order;
            }
        }

        private static void AddTrackCurve(AnimationClip clip, MotionTrackSpec track, Dictionary<string, string> bonePathByName, GameObject targetRoot)
        {
            if (string.IsNullOrEmpty(track.target) || string.IsNullOrEmpty(track.property))
                return;

            if (IsLayerTrack(track))
            {
                var path = FindLayerPath(targetRoot, track.target) ?? track.target;
                if (string.Equals(track.property, "sortingOrder", StringComparison.OrdinalIgnoreCase))
                    clip.SetCurve(path, typeof(SpriteRenderer), "m_SortingOrder", new AnimationCurve(track.keys.ToArray()));
                return;
            }

            if (!bonePathByName.TryGetValue(track.target, out var bonePath))
                bonePath = track.target;
            var transform = targetRoot != null ? targetRoot.transform.Find(bonePath) : null;
            var basePosition = transform != null ? transform.localPosition : Vector3.zero;
            var baseScale = transform != null ? transform.localScale : Vector3.one;
            var baseRotationZ = transform != null ? NormalizeAngle(transform.localEulerAngles.z) : 0f;

            if (string.Equals(track.property, "rotationZ", StringComparison.OrdinalIgnoreCase))
                clip.SetCurve(bonePath, typeof(Transform), "localEulerAnglesRaw.z", Smooth(Offset(track.keys, baseRotationZ)));
            else if (string.Equals(track.property, "positionX", StringComparison.OrdinalIgnoreCase))
                clip.SetCurve(bonePath, typeof(Transform), "localPosition.x", Smooth(Offset(track.keys, basePosition.x)));
            else if (string.Equals(track.property, "positionY", StringComparison.OrdinalIgnoreCase))
                clip.SetCurve(bonePath, typeof(Transform), "localPosition.y", Smooth(Offset(track.keys, basePosition.y)));
            else if (string.Equals(track.property, "scaleY", StringComparison.OrdinalIgnoreCase))
                clip.SetCurve(bonePath, typeof(Transform), "localScale.y", Smooth(Offset(track.keys, baseScale.y)));
        }

        private static Dictionary<string, string> BuildBonePathMap(GameObject root, BoneSpec boneSpec)
        {
            var map = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase);
            if (root != null)
            {
                foreach (var transform in root.GetComponentsInChildren<Transform>(true))
                {
                    var cleanName = transform.name.EndsWith("_1", StringComparison.Ordinal) ? transform.name.Substring(0, transform.name.Length - 2) : transform.name;
                    if (boneSpec.bones.ContainsKey(cleanName) && !map.ContainsKey(cleanName))
                        map[cleanName] = AnimationUtility.CalculateTransformPath(transform, root.transform);
                }
            }
            foreach (var bone in boneSpec.bones.Keys)
            {
                if (!map.ContainsKey(bone))
                    map[bone] = BuildSpecBonePath(bone, boneSpec);
            }
            return map;
        }

        private static string BuildSpecBonePath(string bone, BoneSpec spec)
        {
            var segments = new List<string>();
            var current = bone;
            while (!string.IsNullOrEmpty(current) && spec.bones.ContainsKey(current))
            {
                segments.Add(current);
                current = spec.bones[current].parent;
            }
            segments.Reverse();
            return string.Join("/", segments);
        }

        private static GameObject FindSpecRoot(GameObject selected)
        {
            var current = selected != null ? selected.transform : null;
            while (current != null)
            {
                if (current.GetComponent<Animator>() != null || current.parent == null)
                    return current.gameObject;
                current = current.parent;
            }
            return selected;
        }

        private static GameObject FindSceneRoot(string character)
        {
            var all = UnityEngine.Object.FindObjectsOfType<Transform>(true).Select(transform => transform.gameObject);
            return all.FirstOrDefault(gameObject => !string.IsNullOrEmpty(character) && gameObject.name.Contains(character)) ??
                   all.FirstOrDefault(gameObject => gameObject.GetComponent<Animator>() != null);
        }

        private static string FindLayerPath(GameObject root, string layerName)
        {
            if (root == null)
                return layerName;
            var transform = root.GetComponentsInChildren<Transform>(true).FirstOrDefault(candidate => string.Equals(candidate.name, layerName, StringComparison.OrdinalIgnoreCase));
            return transform != null ? AnimationUtility.CalculateTransformPath(transform, root.transform) : layerName;
        }

        private static IEnumerable<string> FindAvailableSpriteLayerNames(SpecSet spec)
        {
            var psbPath = ResolveAssetPath(spec.folder, spec.layerSpec.psb_path) ?? FindFirstPsbPath(spec.folder);
            var prefab = !string.IsNullOrEmpty(psbPath) ? AssetDatabase.LoadAssetAtPath<GameObject>(psbPath) : null;
            if (prefab == null)
                return Enumerable.Empty<string>();
            return prefab.GetComponentsInChildren<SpriteRenderer>(true)
                .Select(renderer => renderer.sprite != null ? renderer.sprite.name : renderer.name)
                .Where(name => !string.IsNullOrEmpty(name));
        }

        private static IEnumerable<string> TopologicalBoneNames(BoneSpec boneSpec)
        {
            var emitted = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
            while (emitted.Count < boneSpec.bones.Count)
            {
                var progressed = false;
                foreach (var pair in boneSpec.bones)
                {
                    if (emitted.Contains(pair.Key))
                        continue;
                    if (!string.IsNullOrEmpty(pair.Value.parent) && !emitted.Contains(pair.Value.parent))
                        continue;
                    emitted.Add(pair.Key);
                    progressed = true;
                    yield return pair.Key;
                }
                if (!progressed)
                    throw new InvalidDataException("Bone spec contains a parent cycle or missing parent.");
            }
        }

        private static CanvasSpec ParseCanvas(Dictionary<string, object> map)
        {
            return new CanvasSpec
            {
                width = IntValue(map, "width", 2048),
                height = IntValue(map, "height", 2048),
                origin = StringValue(map, "origin", "top_left_pixels")
            };
        }

        private static OutputSpec ParseOutput(Dictionary<string, object> map)
        {
            return new OutputSpec
            {
                prefab_path = StringValue(map, "prefab_path", null),
                clip_folder = StringValue(map, "clip_folder", null),
                controller_path = StringValue(map, "controller_path", null)
            };
        }

        private static List<Keyframe> ParseKeys(IEnumerable<object> keyObjects, float fps)
        {
            var keys = new List<Keyframe>();
            foreach (var keyObject in keyObjects)
            {
                var pair = keyObject as List<object>;
                if (pair == null || pair.Count < 2)
                    continue;
                keys.Add(new Keyframe(Convert.ToSingle(pair[0], CultureInfo.InvariantCulture) / fps, Convert.ToSingle(pair[1], CultureInfo.InvariantCulture)));
            }
            return keys;
        }

        private static Vector3 CanvasPixelToLocal(Vector2 pixel, CanvasSpec canvas, float pixelsPerUnit)
        {
            return new Vector3((pixel.x - canvas.width * 0.5f) / pixelsPerUnit, (canvas.height * 0.5f - pixel.y) / pixelsPerUnit, 0f);
        }

        private static Vector2 ToVector2(float[] values)
        {
            return values != null && values.Length >= 2 ? new Vector2(values[0], values[1]) : Vector2.zero;
        }

        private static float ReadPixelsPerUnit(string path, float fallback)
        {
            var importer = !string.IsNullOrEmpty(path) ? AssetImporter.GetAtPath(path) : null;
            if (importer == null)
                return fallback;
            var serialized = new SerializedObject(importer);
            var property = serialized.FindProperty("m_TextureImporterSettings.m_SpritePixelsPerUnit");
            return property != null && property.floatValue > 0f ? property.floatValue : fallback;
        }

        private static void SaveAnimationClip(AnimationClip clip, string path)
        {
            clip.name = Path.GetFileNameWithoutExtension(path);
            var existing = AssetDatabase.LoadAssetAtPath<AnimationClip>(path);
            if (existing == null)
            {
                AssetDatabase.CreateAsset(clip, path);
                return;
            }
            EditorUtility.CopySerialized(clip, existing);
            existing.name = clip.name;
            EditorUtility.SetDirty(existing);
        }

        private static AnimatorState EnsureState(AnimatorStateMachine stateMachine, string stateName, Motion motion, Vector3 position)
        {
            var child = stateMachine.states.FirstOrDefault(state => state.state.name == stateName);
            var state = child.state ?? stateMachine.AddState(stateName, position);
            state.motion = motion;
            EditorUtility.SetDirty(state);
            return state;
        }

        private static AnimationCurve Smooth(Keyframe[] keys)
        {
            var curve = new AnimationCurve(keys);
            for (var i = 0; i < curve.length; i++)
            {
                AnimationUtility.SetKeyLeftTangentMode(curve, i, AnimationUtility.TangentMode.ClampedAuto);
                AnimationUtility.SetKeyRightTangentMode(curve, i, AnimationUtility.TangentMode.ClampedAuto);
            }
            return curve;
        }

        private static Keyframe[] Offset(IEnumerable<Keyframe> keys, float baseValue)
        {
            return keys.Select(key => new Keyframe(key.time, key.value + baseValue)).ToArray();
        }

        private static float NormalizeAngle(float angle)
        {
            angle %= 360f;
            if (angle > 180f)
                angle -= 360f;
            if (angle < -180f)
                angle += 360f;
            return angle;
        }

        private static bool IsLayerTrack(MotionTrackSpec track)
        {
            return string.Equals(track.target_type, "layer", StringComparison.OrdinalIgnoreCase);
        }

        private static void LogReport(string action, ValidationReport report, string asset)
        {
            Debug.Log("[AI Rig] " + action + " complete. asset: " + asset
                + ", missingLayers: " + Format(report.missingLayers)
                + ", missingBones: " + Format(report.missingBones)
                + ", duplicateLayers: " + Format(report.duplicateLayers)
                + ", duplicateBones: " + Format(report.duplicateBones)
                + ", sortingConflicts: " + Format(report.sortingConflicts)
                + ", motionBindingIssues: " + Format(report.motionBindingIssues));
        }

        private static string Format(IEnumerable<string> values)
        {
            var array = values.Where(value => !string.IsNullOrEmpty(value)).Distinct().ToArray();
            return array.Length == 0 ? "none" : string.Join(", ", array);
        }

        private static void AddDuplicates(IEnumerable<string> values, List<string> output)
        {
            foreach (var group in values.Where(value => !string.IsNullOrEmpty(value)).GroupBy(value => value, StringComparer.OrdinalIgnoreCase))
            {
                if (group.Count() > 1)
                    AddUnique(output, group.Key);
            }
        }

        private static void AddUnique(List<string> list, string value)
        {
            if (!string.IsNullOrEmpty(value) && !list.Contains(value, StringComparer.OrdinalIgnoreCase))
                list.Add(value);
        }

        private static string FindRequiredSpecPath(string folder, string fileName)
        {
            var path = FindOptionalSpecPath(folder, fileName);
            if (string.IsNullOrEmpty(path))
                throw new FileNotFoundException("Missing required spec file: " + fileName, Path.Combine(folder, fileName));
            return path;
        }

        private static string FindOptionalSpecPath(string folder, string fileName)
        {
            var exact = Path.Combine(folder, fileName);
            if (File.Exists(exact))
                return exact;
            var suffix = Directory.GetFiles(folder, "*" + fileName, SearchOption.TopDirectoryOnly).FirstOrDefault();
            return suffix;
        }

        private static string FindFirstPsbPath(string folder)
        {
            var full = Directory.GetFiles(folder, "*.psb", SearchOption.TopDirectoryOnly).FirstOrDefault();
            return FullPathToAssetPath(full);
        }

        private static string ResolveAssetPath(string folder, string path)
        {
            if (string.IsNullOrEmpty(path))
                return null;
            if (path.Replace('\\', '/').StartsWith("Assets/", StringComparison.OrdinalIgnoreCase))
                return path.Replace('\\', '/');
            return FullPathToAssetPath(Path.Combine(folder, path));
        }

        private static string FullPathToAssetPath(string fullPath)
        {
            if (string.IsNullOrEmpty(fullPath))
                return null;
            var normalized = Path.GetFullPath(fullPath).Replace('\\', '/');
            var assets = Path.GetFullPath(Application.dataPath).Replace('\\', '/');
            return normalized.StartsWith(assets, StringComparison.OrdinalIgnoreCase) ? "Assets" + normalized.Substring(assets.Length) : null;
        }

        private static string AssetPathToFullPath(string assetPath)
        {
            if (string.IsNullOrEmpty(assetPath))
                return null;
            if (!assetPath.Replace('\\', '/').StartsWith("Assets/", StringComparison.OrdinalIgnoreCase))
                return assetPath;
            return Path.GetFullPath(Path.Combine(Application.dataPath, assetPath.Substring("Assets/".Length)));
        }

        private static void EnsureAssetFolder(string folder)
        {
            if (string.IsNullOrEmpty(folder) || AssetDatabase.IsValidFolder(folder))
                return;
            var parent = Path.GetDirectoryName(folder).Replace('\\', '/');
            EnsureAssetFolder(parent);
            AssetDatabase.CreateFolder(parent, Path.GetFileName(folder));
        }

        private static string SanitizeAssetName(string name)
        {
            return string.Join("_", (string.IsNullOrEmpty(name) ? "Clip" : name).Split(Path.GetInvalidFileNameChars()));
        }

        private static Dictionary<string, object> ObjectValue(Dictionary<string, object> map, string key)
        {
            return map != null && map.TryGetValue(key, out var value) ? value as Dictionary<string, object> ?? new Dictionary<string, object>() : new Dictionary<string, object>();
        }

        private static IEnumerable<object> ArrayValue(Dictionary<string, object> map, string key)
        {
            return map != null && map.TryGetValue(key, out var value) ? value as List<object> ?? Enumerable.Empty<object>() : Enumerable.Empty<object>();
        }

        private static string StringValue(Dictionary<string, object> map, string key, string fallback)
        {
            if (map == null || !map.TryGetValue(key, out var value) || value == null)
                return fallback;
            return value as string ?? Convert.ToString(value, CultureInfo.InvariantCulture);
        }

        private static bool BoolValue(Dictionary<string, object> map, string key, bool fallback)
        {
            if (map == null || !map.TryGetValue(key, out var value) || value == null)
                return fallback;
            return value is bool boolValue ? boolValue : fallback;
        }

        private static int IntValue(Dictionary<string, object> map, string key, int fallback)
        {
            if (map == null || !map.TryGetValue(key, out var value) || value == null)
                return fallback;
            return Convert.ToInt32(value, CultureInfo.InvariantCulture);
        }

        private static float FloatValue(Dictionary<string, object> map, string key, float fallback)
        {
            if (map == null || !map.TryGetValue(key, out var value) || value == null)
                return fallback;
            return Convert.ToSingle(value, CultureInfo.InvariantCulture);
        }

        private static float[] FloatArray(Dictionary<string, object> map, string key)
        {
            if (map == null || !map.TryGetValue(key, out var value))
                return Array.Empty<float>();
            var list = value as List<object>;
            return list == null ? Array.Empty<float>() : list.Select(item => Convert.ToSingle(item, CultureInfo.InvariantCulture)).ToArray();
        }

        private sealed class Json
        {
            private readonly string text;
            private int index;

            private Json(string text)
            {
                this.text = text;
            }

            public static object Parse(string text)
            {
                return new Json(text).ReadValue();
            }

            private object ReadValue()
            {
                SkipWhitespace();
                if (index >= text.Length)
                    return null;
                var c = text[index];
                if (c == '{') return ReadObject();
                if (c == '[') return ReadArray();
                if (c == '"') return ReadString();
                if (char.IsDigit(c) || c == '-') return ReadNumber();
                if (Match("true")) return true;
                if (Match("false")) return false;
                if (Match("null")) return null;
                throw new InvalidDataException("Invalid JSON near index " + index);
            }

            private Dictionary<string, object> ReadObject()
            {
                var map = new Dictionary<string, object>(StringComparer.OrdinalIgnoreCase);
                index++;
                SkipWhitespace();
                while (index < text.Length && text[index] != '}')
                {
                    var key = ReadString();
                    SkipWhitespace();
                    Expect(':');
                    map[key] = ReadValue();
                    SkipWhitespace();
                    if (index < text.Length && text[index] == ',')
                    {
                        index++;
                        SkipWhitespace();
                    }
                }
                Expect('}');
                return map;
            }

            private List<object> ReadArray()
            {
                var list = new List<object>();
                index++;
                SkipWhitespace();
                while (index < text.Length && text[index] != ']')
                {
                    list.Add(ReadValue());
                    SkipWhitespace();
                    if (index < text.Length && text[index] == ',')
                    {
                        index++;
                        SkipWhitespace();
                    }
                }
                Expect(']');
                return list;
            }

            private string ReadString()
            {
                Expect('"');
                var result = new System.Text.StringBuilder();
                while (index < text.Length)
                {
                    var c = text[index++];
                    if (c == '"')
                        return result.ToString();
                    if (c == '\\' && index < text.Length)
                    {
                        var escaped = text[index++];
                        if (escaped == '"' || escaped == '\\' || escaped == '/')
                            result.Append(escaped);
                        else if (escaped == 'n')
                            result.Append('\n');
                        else if (escaped == 'r')
                            result.Append('\r');
                        else if (escaped == 't')
                            result.Append('\t');
                    }
                    else
                    {
                        result.Append(c);
                    }
                }
                throw new InvalidDataException("Unterminated JSON string.");
            }

            private object ReadNumber()
            {
                var start = index;
                while (index < text.Length && "-+0123456789.eE".IndexOf(text[index]) >= 0)
                    index++;
                var slice = text.Substring(start, index - start);
                return slice.IndexOfAny(new[] { '.', 'e', 'E' }) >= 0
                    ? (object)double.Parse(slice, CultureInfo.InvariantCulture)
                    : long.Parse(slice, CultureInfo.InvariantCulture);
            }

            private bool Match(string value)
            {
                if (string.Compare(text, index, value, 0, value.Length, StringComparison.Ordinal) != 0)
                    return false;
                index += value.Length;
                return true;
            }

            private void Expect(char c)
            {
                SkipWhitespace();
                if (index >= text.Length || text[index] != c)
                    throw new InvalidDataException("Expected '" + c + "' near index " + index);
                index++;
            }

            private void SkipWhitespace()
            {
                while (index < text.Length && char.IsWhiteSpace(text[index]))
                    index++;
            }
        }
    }
}
```

## SpecDrivenRigBuilderTests.cs

```csharp
using NUnit.Framework;
using System.IO;
using System.Linq;
using UnityEngine;

namespace NovaBot.Editor
{
    public sealed class SpecDrivenRigBuilderTests
    {
        [Test]
        public void LoadSpecSet_SupportsNearFarNamesWithoutLeftRight()
        {
            var folder = CreateSpecFolder("near_far");
            WriteText(folder, "bone_spec.json", @"{
  ""character"": ""Bot"",
  ""pose"": ""ThreeQuarter"",
  ""canvas"": { ""width"": 1000, ""height"": 1000 },
  ""output"": { ""prefab_path"": ""Assets/Temp/Bot.prefab"", ""clip_folder"": ""Assets/Temp"" },
  ""bones"": {
    ""root"": { ""parent"": null, ""head_px"": [500, 800], ""tail_px"": [500, 700] },
    ""arm_near"": { ""parent"": ""root"", ""head_px"": [430, 660], ""tail_px"": [360, 760] },
    ""arm_far"": { ""parent"": ""root"", ""head_px"": [570, 660], ""tail_px"": [640, 760] }
  }
}");
            WriteText(folder, "layer_spec.json", @"{
  ""psb_path"": ""Assets/Art/Characters/NovaBot/NovaBot_layers.psb"",
  ""layers"": [
    { ""name"": ""upper_arm_near"", ""bone"": ""arm_near"" },
    { ""name"": ""upper_arm_far"", ""bone"": ""arm_far"" }
  ]
}");
            WriteText(folder, "sorting_spec.json", @"{ ""orders"": [
  { ""layer"": ""upper_arm_far"", ""order"": 5 },
  { ""layer"": ""upper_arm_near"", ""order"": 15 }
]}");
            WriteText(folder, "motion_spec.json", @"{ ""clips"": [
  { ""name"": ""Run"", ""path"": ""Assets/Temp/Bot_Run.anim"", ""fps"": 24, ""duration"": 0.5, ""loop"": true,
    ""tracks"": [
      { ""target"": ""arm_near"", ""property"": ""rotationZ"", ""keys"": [[0, 0], [6, 2], [12, 0]] },
      { ""target"": ""upper_arm_near"", ""target_type"": ""layer"", ""property"": ""sortingOrder"", ""keys"": [[0, 15], [6, 5], [12, 15]] }
    ] }
]}");

            var spec = SpecDrivenRigBuilder.LoadSpecSet(folder);

            Assert.That(spec.boneSpec.pose, Is.EqualTo("ThreeQuarter"));
            Assert.That(spec.boneSpec.bones.ContainsKey("arm_near"), Is.True);
            Assert.That(spec.layerSpec.layers[0].bone, Is.EqualTo("arm_near"));
            Assert.That(spec.motionSpec.clips[0].tracks[0].target, Is.EqualTo("arm_near"));
        }

        [Test]
        public void ValidateSpecSet_ReportsMissingBonesDuplicateLayersAndSortingConflicts()
        {
            var folder = CreateSpecFolder("invalid");
            WriteText(folder, "bone_spec.json", @"{
  ""character"": ""Bot"",
  ""canvas"": { ""width"": 1000, ""height"": 1000 },
  ""bones"": {
    ""root"": { ""parent"": null, ""head_px"": [500, 800], ""tail_px"": [500, 700] },
    ""arm_near"": { ""parent"": ""missing_parent"", ""head_px"": [430, 660], ""tail_px"": [360, 760] }
  }
}");
            WriteText(folder, "layer_spec.json", @"{ ""layers"": [
  { ""name"": ""arm"", ""bone"": ""arm_near"" },
  { ""name"": ""arm"", ""bone"": ""missing_bone"" }
]}");
            WriteText(folder, "sorting_spec.json", @"{ ""orders"": [
  { ""layer"": ""arm"", ""order"": 3 },
  { ""layer"": ""leg"", ""order"": 3 }
]}");
            WriteText(folder, "motion_spec.json", @"{ ""clips"": [
  { ""name"": ""Idle"", ""tracks"": [
    { ""target"": ""missing_motion_bone"", ""property"": ""rotationZ"", ""keys"": [[0, 0]] },
    { ""target"": ""missing_layer"", ""target_type"": ""layer"", ""property"": ""sortingOrder"", ""keys"": [[0, 1]] }
  ] }
]}");

            var report = SpecDrivenRigBuilder.ValidateSpecSet(SpecDrivenRigBuilder.LoadSpecSet(folder), Enumerable.Empty<string>());

            Assert.That(report.missingBones, Does.Contain("missing_parent"));
            Assert.That(report.missingBones, Does.Contain("missing_bone"));
            Assert.That(report.missingBones, Does.Contain("missing_motion_bone"));
            Assert.That(report.duplicateLayers, Does.Contain("arm"));
            Assert.That(report.sortingConflicts.Any(conflict => conflict.Contains("order 3")), Is.True);
            Assert.That(report.missingLayers, Does.Contain("missing_layer"));
        }

        [Test]
        public void CreateBoneHierarchy_UsesSpecCanvasAndTopLeftCoordinates()
        {
            var boneSpec = new SpecDrivenRigBuilder.BoneSpec
            {
                canvas = new SpecDrivenRigBuilder.CanvasSpec { width = 1000, height = 1000 },
                bones = {
                    { "root", new SpecDrivenRigBuilder.BoneEntry { parent = null, head_px = new[] { 500f, 800f }, tail_px = new[] { 500f, 700f } } },
                    { "arm_near", new SpecDrivenRigBuilder.BoneEntry { parent = "root", head_px = new[] { 450f, 700f }, tail_px = new[] { 400f, 780f } } }
                }
            };
            var root = new GameObject("Rig");
            try
            {
                var bones = SpecDrivenRigBuilder.CreateBoneHierarchy(root, boneSpec, 100f);

                Assert.That(bones["root"].localPosition, Is.EqualTo(new Vector3(0f, -3f, 0f)));
                Assert.That(bones["arm_near"].parent, Is.EqualTo(bones["root"]));
                Assert.That(bones["arm_near"].position.x, Is.EqualTo(-0.5f).Within(0.0001f));
                Assert.That(bones["arm_near"].position.y, Is.EqualTo(-2f).Within(0.0001f));
            }
            finally
            {
                Object.DestroyImmediate(root);
            }
        }

        private static string CreateSpecFolder(string name)
        {
            var folder = Path.Combine(Application.dataPath, "../Temp/SpecDrivenRigBuilderTests", name);
            if (Directory.Exists(folder))
                Directory.Delete(folder, true);
            Directory.CreateDirectory(folder);
            return folder;
        }

        private static void WriteText(string folder, string fileName, string contents)
        {
            File.WriteAllText(Path.Combine(folder, fileName), contents);
        }
    }
}
```
