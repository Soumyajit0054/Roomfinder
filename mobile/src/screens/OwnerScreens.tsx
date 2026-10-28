import React, { useCallback, useEffect, useState } from "react";
import {
  ActivityIndicator, Alert, FlatList, Image, KeyboardAvoidingView, Linking, Platform, Pressable,
  RefreshControl, ScrollView, Switch, Text, View,
} from "react-native";
import { useFocusEffect } from "@react-navigation/native";
import * as ImagePicker from "expo-image-picker";
import { Picker } from "@react-native-picker/picker";
import { api, OwnerProperty, OwnerRequest, Property } from "../api";
import { confirm, errorMessage, useList } from "../hooks";
import Icon from "../Icon";
import { Button, colors, Empty, ErrorText, Eyebrow, Field, PropertyCard, Row, StatCard, StatusBadge } from "../ui";

// ---------------------------------------------------------------- dashboard

export function OwnerDashboardScreen({ navigation }: any) {
  const [stats, setStats] = useState<{ property_count: number; available_count: number; pending_count: number } | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useFocusEffect(useCallback(() => {
    api.ownerDashboard().then(setStats).catch((e) => setErr(errorMessage(e, "Could not load.")));
  }, []));

  return (
    <ScrollView style={{ backgroundColor: colors.bg }} contentContainerStyle={{ padding: 16 }}>
      <Eyebrow>Owner dashboard</Eyebrow>
      <Text style={{ fontSize: 28, fontWeight: "800", color: colors.text, marginBottom: 16 }}>Manage your listings</Text>
      <ErrorText>{err}</ErrorText>
      {!stats && !err && <ActivityIndicator color={colors.primary} />}
      {stats && (
        <View style={{ gap: 12 }}>
          <StatCard label="Total Properties" value={stats.property_count} icon="houses" tone="blue" />
          <StatCard label="Available Properties" value={stats.available_count} icon="house-check" tone="green" />
          <StatCard label="Pending Requests" value={stats.pending_count} icon="clock" tone="gold" />
        </View>
      )}
      <View style={{ marginTop: 24, gap: 12 }}>
        <Button title="Add a property" icon="house-add" onPress={() => navigation.navigate("PropertyForm", {})} />
        <Button title="Review rental requests" icon="send" variant="outline" onPress={() => navigation.navigate("OwnerRequests")} />
      </View>
    </ScrollView>
  );
}

// ---------------------------------------------------------------- my properties

const fetchOwnerProps = () => api.ownerProperties().then((r) => r.properties);

export function OwnerPropertiesScreen({ navigation }: any) {
  const { items, loading, err, load } = useList<Property>(fetchOwnerProps);

  const remove = (p: Property) =>
    confirm("Delete property", `Delete "${p.title}" and its photos? This cannot be undone.`, "Delete", async () => {
      try { await api.ownerDeleteProperty(p.id); load(); }
      catch (e) { Alert.alert("Error", errorMessage(e)); }
    });

  if (loading) return <ActivityIndicator style={{ marginTop: 40 }} color={colors.primary} />;
  return (
    <View style={{ flex: 1, backgroundColor: colors.bg }}>
      <FlatList
        contentContainerStyle={{ padding: 16 }}
        data={items} keyExtractor={(p) => String(p.id)}
        refreshControl={<RefreshControl refreshing={false} onRefresh={load} />}
        ListHeaderComponent={<ErrorText>{err}</ErrorText>}
        ListEmptyComponent={<Empty icon="house-add" text="You haven't listed any properties yet." />}
        renderItem={({ item }) => (
          <View>
            <PropertyCard item={item} onPress={() => navigation.navigate("Property", { id: item.id })} />
            <View style={{ flexDirection: "row", gap: 10, marginTop: -6, marginBottom: 18 }}>
              <View style={{ flex: 1 }}><Button title="Edit" icon="pencil-square" variant="outline" onPress={() => navigation.navigate("PropertyForm", { id: item.id })} /></View>
              <View style={{ flex: 1 }}><Button title="Delete" icon="trash3" variant="outline" onPress={() => remove(item)} /></View>
            </View>
          </View>
        )}
      />
      <Pressable accessibilityLabel="Add property" onPress={() => navigation.navigate("PropertyForm", {})}
        style={{ position: "absolute", right: 20, bottom: 24, width: 56, height: 56, borderRadius: 28, backgroundColor: colors.primary, alignItems: "center", justifyContent: "center", elevation: 5 }}>
        <Icon name="plus-circle" size={26} color="#fff" />
      </Pressable>
    </View>
  );
}

// ---------------------------------------------------------------- add / edit form

type FormState = {
  title: string; description: string; location: string; address: string; rent: string;
  room_type: string; furnished: string; food_available: string; gender_preference: string; available: boolean;
};
const EMPTY: FormState = {
  title: "", description: "", location: "", address: "", rent: "",
  room_type: "Single", furnished: "No", food_available: "No", gender_preference: "Any", available: true,
};

const Select = ({ label, value, onChange, options }: { label: string; value: string; onChange: (v: string) => void; options: string[] }) => (
  <View style={{ marginBottom: 8 }}>
    <Text style={{ fontWeight: "600" }}>{label}</Text>
    <Picker selectedValue={value} onValueChange={onChange}>
      {options.map((o) => <Picker.Item key={o} label={o} value={o} />)}
    </Picker>
  </View>
);

export function PropertyFormScreen({ route, navigation }: any) {
  const id: number | null = route.params?.id ?? null;
  const [f, setF] = useState<FormState>(EMPTY);
  const [existing, setExisting] = useState<{ id: number; url: string }[]>([]);
  const [removed, setRemoved] = useState<number[]>([]);
  const [added, setAdded] = useState<ImagePicker.ImagePickerAsset[]>([]);
  const [loading, setLoading] = useState(!!id);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const set = <K extends keyof FormState>(k: K) => (v: FormState[K]) => setF((p) => ({ ...p, [k]: v }));

  useEffect(() => {
    navigation.setOptions({ title: id ? "Edit property" : "Add property" });
    if (!id) return;
    api.ownerProperty(id).then(({ property: p }: { property: OwnerProperty }) => {
      setF({
        title: p.title, description: p.description ?? "", location: p.location, address: p.address ?? "",
        rent: String(p.rent), room_type: p.room_type, furnished: p.furnished ?? "No",
        food_available: p.food_available ?? "No", gender_preference: p.gender_preference ?? "Any", available: p.available,
      });
      setExisting(p.image_items);
    }).catch((e) => setErr(errorMessage(e))).finally(() => setLoading(false));
  }, [id, navigation]);

  const pickImages = async () => {
    const perm = await ImagePicker.requestMediaLibraryPermissionsAsync();
    if (!perm.granted) return Alert.alert("Permission needed", "Allow photo access to attach pictures.");
    const res = await ImagePicker.launchImageLibraryAsync({ mediaTypes: ["images"], allowsMultipleSelection: true, selectionLimit: 10, quality: 0.8 });
    if (!res.canceled) setAdded((prev) => [...prev, ...res.assets].slice(0, 10));
  };

  const submit = async () => {
    if (!f.title.trim()) return setErr("Property title is required.");
    if (!f.location.trim()) return setErr("Property location is required.");
    if (!(parseFloat(f.rent) > 0)) return setErr("Enter a rent greater than 0.");
    setBusy(true); setErr(null);
    try {
      const form = new FormData();
      (Object.keys(f) as (keyof FormState)[]).forEach((k) => form.append(k, k === "available" ? (f.available ? "1" : "0") : String(f[k])));
      removed.forEach((r) => form.append("delete_image_ids", String(r)));
      added.forEach((a, i) => {
        const ext = (a.uri.split(".").pop() ?? "jpg").toLowerCase().replace(/[^a-z0-9]/g, "") || "jpg";
        form.append("images", { uri: a.uri, name: a.fileName ?? `photo_${i}.${ext}`, type: a.mimeType ?? `image/${ext === "jpg" ? "jpeg" : ext}` } as any);
      });
      const res = await api.ownerSaveProperty(id, form);
      if (res.images_rejected.length) Alert.alert("Some photos were skipped", res.images_rejected.join("\n"));
      navigation.goBack();
    } catch (e) { setErr(errorMessage(e)); }
    finally { setBusy(false); }
  };

  if (loading) return <ActivityIndicator style={{ marginTop: 40 }} color={colors.primary} />;
  const kept = existing.filter((x) => !removed.includes(x.id));

  return (
    <KeyboardAvoidingView style={{ flex: 1 }} behavior={Platform.OS === "ios" ? "padding" : undefined}>
      <ScrollView style={{ backgroundColor: colors.bg }} contentContainerStyle={{ padding: 16 }} keyboardShouldPersistTaps="handled">
        <Field label="Title *" value={f.title} onChangeText={set("title")} />
        <Field label="Location *" value={f.location} onChangeText={set("location")} placeholder="Area or city" />
        <Field label="Address" value={f.address} onChangeText={set("address")} />
        <Field label="Monthly rent *" value={f.rent} onChangeText={set("rent")} keyboardType="decimal-pad" />
        <Field label="Description" value={f.description} onChangeText={set("description")} multiline style={{ minHeight: 90, textAlignVertical: "top", paddingTop: 10 }} />
        <Select label="Room type" value={f.room_type} onChange={set("room_type")} options={["Single", "Double", "PG", "1BHK"]} />
        <Select label="Furnished" value={f.furnished} onChange={set("furnished")} options={["Yes", "No"]} />
        <Select label="Food available" value={f.food_available} onChange={set("food_available")} options={["Yes", "No"]} />
        <Select label="Gender preference" value={f.gender_preference} onChange={set("gender_preference")} options={["Any", "Male", "Female"]} />
        {!!id && (
          <View style={{ flexDirection: "row", alignItems: "center", justifyContent: "space-between", marginBottom: 12 }}>
            <Text style={{ fontWeight: "600" }}>Available for rent</Text>
            <Switch value={f.available} onValueChange={set("available")} />
          </View>
        )}

        <Text style={{ fontWeight: "600", marginBottom: 6 }}>Photos</Text>
        <View style={{ flexDirection: "row", flexWrap: "wrap", gap: 8, marginBottom: 10 }}>
          {kept.map((img) => (
            <Pressable key={img.id} onPress={() => setRemoved((r) => [...r, img.id])} accessibilityLabel="Remove photo">
              <Image source={{ uri: img.url }} style={{ width: 90, height: 90, borderRadius: 8 }} />
              <Text style={{ position: "absolute", right: 4, top: 2, color: "#fff", fontWeight: "800", textShadowColor: "#000", textShadowRadius: 3 }}>✕</Text>
            </Pressable>
          ))}
          {added.map((a, i) => (
            <Pressable key={a.uri} onPress={() => setAdded((x) => x.filter((_, j) => j !== i))} accessibilityLabel="Remove new photo">
              <Image source={{ uri: a.uri }} style={{ width: 90, height: 90, borderRadius: 8, borderWidth: 2, borderColor: colors.primary }} />
              <Text style={{ position: "absolute", right: 4, top: 2, color: "#fff", fontWeight: "800", textShadowColor: "#000", textShadowRadius: 3 }}>✕</Text>
            </Pressable>
          ))}
        </View>
        <Text style={{ color: colors.muted, fontSize: 12, marginBottom: 8 }}>Tap a photo to remove it.</Text>
        <Button title="Add photos" icon="images" variant="outline" onPress={pickImages} />

        <View style={{ height: 16 }} />
        <ErrorText>{err}</ErrorText>
        <Button title={id ? "Save changes" : "Add property"} icon="check2" onPress={submit} loading={busy} />
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

// ---------------------------------------------------------------- requests

const fetchOwnerReqs = () => api.ownerRequests().then((r) => r.requests);

export function OwnerRequestsScreen({ navigation }: any) {
  const { items, loading, err, load } = useList<OwnerRequest>(fetchOwnerReqs);
  const [busyId, setBusyId] = useState<number | null>(null);

  const decide = (r: OwnerRequest, status: "accepted" | "rejected") => {
    const run = async () => {
      setBusyId(r.id);
      try { await api.ownerDecide(r.id, status); await load(); }
      catch (e) { Alert.alert("Error", errorMessage(e)); }
      finally { setBusyId(null); }
    };
    if (status === "accepted") {
      confirm("Accept request", `Accepting marks "${r.property.title}" as no longer available.`, "Accept", run);
    } else run();
  };

  if (loading) return <ActivityIndicator style={{ marginTop: 40 }} color={colors.primary} />;
  return (
    <FlatList
      style={{ backgroundColor: colors.bg }} contentContainerStyle={{ padding: 16 }}
      data={items} keyExtractor={(r) => String(r.id)}
      refreshControl={<RefreshControl refreshing={false} onRefresh={load} />}
      ListHeaderComponent={<ErrorText>{err}</ErrorText>}
      ListEmptyComponent={<Empty icon="send" text="No rental requests yet." />}
      renderItem={({ item: r }) => (
        <Row>
          <Text style={{ fontWeight: "700", fontSize: 16 }} onPress={() => navigation.navigate("Property", { id: r.property.id })}>{r.property.title}</Text>
          <Text style={{ color: colors.muted }}>{r.property.location} · {r.property.rent.toLocaleString()} / month</Text>
          <View style={{ marginTop: 8 }}>
            <View style={{ flexDirection: "row", alignItems: "center", gap: 6 }}><Icon name="person-fill" size={14} color={colors.primary} /><Text style={{ fontWeight: "700" }}>{r.tenant.name}</Text></View>
            <Text style={{ color: colors.muted }}>{r.tenant.email}</Text>
            {!!r.tenant.phone && <Text style={{ color: colors.primary }} onPress={() => Linking.openURL(`tel:${r.tenant.phone}`)}>{r.tenant.phone}</Text>}
          </View>
          {!!r.message && <Text style={{ marginTop: 8, fontStyle: "italic" }}>"{r.message}"</Text>}
          <View style={{ marginTop: 8 }}><StatusBadge status={r.status} /></View>
          {r.status === "pending" && (
            <View style={{ flexDirection: "row", gap: 10, marginTop: 10 }}>
              <View style={{ flex: 1 }}><Button title="Accept" icon="check-circle" loading={busyId === r.id} onPress={() => decide(r, "accepted")} /></View>
              <View style={{ flex: 1 }}><Button title="Reject" icon="x-circle" variant="outline" disabled={busyId === r.id} onPress={() => decide(r, "rejected")} /></View>
            </View>
          )}
        </Row>
      )}
    />
  );
}
