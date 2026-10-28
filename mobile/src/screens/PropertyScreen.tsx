import React, { useEffect, useState } from "react";
import { ActivityIndicator, Alert, Dimensions, FlatList, Image, Linking, ScrollView, Text, TextInput, View } from "react-native";
import { api, ApiError, Property } from "../api";
import { useAuth } from "../auth";
import Icon, { IconName } from "../Icon";
import { Button, Center, colors, ErrorText, IconTile, Pill, Row } from "../ui";

const W = Dimensions.get("window").width;

const Detail = ({ icon, label, value }: { icon: IconName; label: string; value?: string | null }) =>
  value ? (
    <View style={{ flexBasis: "47%", flexGrow: 1, flexDirection: "row", alignItems: "center", gap: 10 }}>
      <IconTile name={icon} size={40} />
      <View style={{ flex: 1 }}>
        <Text style={{ color: colors.muted, fontSize: 12 }}>{label}</Text>
        <Text style={{ fontWeight: "700", color: colors.text }}>{value}</Text>
      </View>
    </View>
  ) : null;

export default function PropertyScreen({ route }: any) {
  const { id } = route.params as { id: number };
  const { user } = useAuth();
  const isTenant = user?.role === "tenant";
  const [p, setP] = useState<Property | null>(null);
  const [fav, setFav] = useState(false);
  const [message, setMessage] = useState("");
  const [err, setErr] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [page, setPage] = useState(0);

  useEffect(() => {
    api.property(id).then((r) => setP(r.property)).catch((e) => setErr(e.message));
    if (isTenant) api.favorites().then((r) => setFav(r.properties.some((x) => x.id === id))).catch(() => {});
  }, [id, isTenant]);

  const toggleFav = async () => {
    const next = !fav;
    setFav(next); // optimistic
    try { await (next ? api.addFavorite(id) : api.removeFavorite(id)); }
    catch (e) { setFav(!next); Alert.alert("Error", e instanceof ApiError ? e.message : "Try again."); }
  };

  const send = async () => {
    setBusy(true); setErr(null);
    try {
      await api.sendRequest(id, message);
      setMessage("");
      Alert.alert("Sent", "Your rental request was sent to the owner.");
    } catch (e) { setErr(e instanceof ApiError ? e.message : "Something went wrong."); }
    finally { setBusy(false); }
  };

  if (!p) return <Center>{err ? <ErrorText>{err}</ErrorText> : <ActivityIndicator color={colors.primary} />}</Center>;

  const photos = p.images?.length ? p.images : p.image ? [p.image] : [];

  return (
    <ScrollView style={{ backgroundColor: colors.bg }} keyboardShouldPersistTaps="handled" contentContainerStyle={{ paddingBottom: 40 }}>
      <View>
        {photos.length ? (
          <FlatList horizontal pagingEnabled data={photos} keyExtractor={(u) => u} showsHorizontalScrollIndicator={false}
            onMomentumScrollEnd={(e) => setPage(Math.round(e.nativeEvent.contentOffset.x / W))}
            renderItem={({ item }) => <Image source={{ uri: item }} style={{ width: W, height: 260 }} />} />
        ) : (
          <View style={{ width: W, height: 200, backgroundColor: colors.tintBlue, alignItems: "center", justifyContent: "center" }}>
            <Icon name="house" size={56} color={colors.primary} />
          </View>
        )}
        {photos.length > 1 && (
          <View style={{ position: "absolute", right: 12, bottom: 12, flexDirection: "row", gap: 6, alignItems: "center", backgroundColor: "#000a", paddingHorizontal: 10, paddingVertical: 5, borderRadius: 999 }}>
            <Icon name="images" size={13} color="#fff" />
            <Text style={{ color: "#fff", fontWeight: "700", fontSize: 12 }}>{page + 1} / {photos.length}</Text>
          </View>
        )}
      </View>

      <View style={{ padding: 16 }}>
        <View style={{ flexDirection: "row", gap: 8, marginBottom: 8 }}>
          <Pill label={p.available ? "Available" : "Taken"} color="#fff" bg={p.available ? colors.success : colors.muted} />
          <Pill label={p.room_type} />
        </View>
        <Text style={{ fontSize: 24, fontWeight: "800", color: colors.text }}>{p.title}</Text>
        <View style={{ flexDirection: "row", alignItems: "center", gap: 6, marginTop: 6 }}>
          <Icon name="geo-alt-fill" size={15} color={colors.primary} />
          <Text style={{ color: colors.muted, flex: 1 }}>{[p.location, p.address].filter(Boolean).join(" · ")}</Text>
        </View>
        <Text style={{ color: colors.primary, fontSize: 28, fontWeight: "800", marginTop: 12 }}>
          ₹{p.rent.toLocaleString()}<Text style={{ fontSize: 14, color: colors.muted, fontWeight: "500" }}> / month</Text>
        </Text>

        <Row style={{ marginTop: 16, flexDirection: "row", flexWrap: "wrap", gap: 14 }}>
          <Detail icon="door-open" label="Room type" value={p.room_type} />
          <Detail icon="box-seam" label="Furnished" value={p.furnished} />
          <Detail icon="cup-hot" label="Food available" value={p.food_available} />
          <Detail icon="people" label="Preferred" value={p.gender_preference} />
        </Row>

        {!!p.description && (
          <Row>
            <Text style={{ fontWeight: "800", fontSize: 16, marginBottom: 6 }}>About this place</Text>
            <Text style={{ lineHeight: 22, color: colors.text }}>{p.description}</Text>
          </Row>
        )}

        <Row>
          <Text style={{ fontWeight: "800", fontSize: 16, marginBottom: 10 }}>Listed by</Text>
          <View style={{ flexDirection: "row", alignItems: "center", gap: 12 }}>
            <IconTile name="person-fill" size={44} />
            <Text style={{ fontWeight: "700", fontSize: 16 }}>{p.owner_name}</Text>
          </View>
          {(p.owner_phone || p.owner_email) && (
            <View style={{ flexDirection: "row", gap: 10, marginTop: 12 }}>
              {!!p.owner_phone && <View style={{ flex: 1 }}><Button title="Call" icon="telephone" variant="outline" onPress={() => Linking.openURL(`tel:${p.owner_phone}`)} /></View>}
              {!!p.owner_email && <View style={{ flex: 1 }}><Button title="Email" icon="envelope" variant="outline" onPress={() => Linking.openURL(`mailto:${p.owner_email}`)} /></View>}
            </View>
          )}
        </Row>

        {isTenant && (
          <Row>
            <Text style={{ fontWeight: "800", fontSize: 16, marginBottom: 10 }}>Interested in this room?</Text>
            <Button title={fav ? "Saved to favorites" : "Save to favorites"} icon={fav ? "heart-fill" : "heart"} variant="outline" onPress={toggleFav} />
            <TextInput value={message} onChangeText={setMessage} multiline maxLength={1000} placeholder="Introduce yourself to the owner (optional)"
              placeholderTextColor={colors.muted}
              style={{ backgroundColor: "#fff", borderWidth: 1, borderColor: colors.border, borderRadius: 10, padding: 12, minHeight: 90, textAlignVertical: "top", marginVertical: 12, fontSize: 15 }} />
            <ErrorText>{err}</ErrorText>
            <Button title="Send rental request" icon="send" onPress={send} loading={busy} disabled={!p.available} />
            {!p.available && <Text style={{ color: colors.warning, marginTop: 8 }}>This room is no longer available.</Text>}
          </Row>
        )}
      </View>
    </ScrollView>
  );
}
