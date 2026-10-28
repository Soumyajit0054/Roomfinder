import React, { useCallback, useEffect, useRef, useState } from "react";
import { ActivityIndicator, FlatList, Pressable, RefreshControl, Text, View } from "react-native";
import { Picker } from "@react-native-picker/picker";
import { api, ApiError, Property } from "../api";
import Icon from "../Icon";
import { colors, Empty, ErrorText, Eyebrow, PropertyCard, SearchInput } from "../ui";

const PAGE = 20;

export default function BrowseScreen({ navigation }: any) {
  const [items, setItems] = useState<Property[]>([]);
  const [location, setLocation] = useState("");
  const [minRent, setMinRent] = useState("");
  const [maxRent, setMaxRent] = useState("");
  const [roomType, setRoomType] = useState("");
  const [furnished, setFurnished] = useState("");
  const [showFilters, setShowFilters] = useState(false);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [more, setMore] = useState(true);
  const [err, setErr] = useState<string | null>(null);
  const reqId = useRef(0);

  const load = useCallback(async (reset: boolean, current: Property[] = []) => {
    const id = ++reqId.current; // ignore out-of-order responses while typing
    setErr(null);
    try {
      const res = await api.properties({
        location: location.trim(), min_rent: minRent.trim(), max_rent: maxRent.trim(),
        room_type: roomType, furnished,
        limit: PAGE, offset: reset ? 0 : current.length,
      });
      if (id !== reqId.current) return;
      setItems(reset ? res.properties : [...current, ...res.properties]);
      setMore(res.properties.length === PAGE);
    } catch (e) {
      if (id === reqId.current) setErr(e instanceof ApiError ? e.message : "Could not load rooms.");
    } finally {
      if (id === reqId.current) { setLoading(false); setRefreshing(false); }
    }
  }, [location, minRent, maxRent, roomType, furnished]);

  useEffect(() => {
    setLoading(true);
    const t = setTimeout(() => load(true), 350); // debounce filters
    return () => clearTimeout(t);
  }, [load]);

  const activeFilters = [minRent, maxRent, roomType, furnished].filter(Boolean).length;

  const header = (
    <View style={{ marginBottom: 8 }}>
      <Eyebrow>Find rooms</Eyebrow>
      <Text style={{ fontSize: 24, fontWeight: "800", color: colors.text, marginBottom: 12 }}>Search properties</Text>
      <View style={{ flexDirection: "row", gap: 10 }}>
        <View style={{ flex: 1 }}><SearchInput placeholder="Search by location" value={location} onChangeText={setLocation} /></View>
        <Pressable onPress={() => setShowFilters((v) => !v)} accessibilityLabel="Filters"
          style={{ width: 50, height: 50, borderRadius: 10, backgroundColor: showFilters || activeFilters ? colors.primary : "#fff", borderWidth: 1, borderColor: showFilters || activeFilters ? colors.primary : colors.border, alignItems: "center", justifyContent: "center" }}>
          <Icon name="sliders" size={18} color={showFilters || activeFilters ? "#fff" : colors.primary} />
        </Pressable>
      </View>
      {showFilters && (
        <View style={{ backgroundColor: "#fff", borderRadius: 14, padding: 12, marginTop: 10, borderWidth: 1, borderColor: colors.border }}>
          <View style={{ flexDirection: "row", gap: 10 }}>
            <View style={{ flex: 1 }}><SearchInput placeholder="Min ₹" value={minRent} onChangeText={setMinRent} keyboardType="numeric" /></View>
            <View style={{ flex: 1 }}><SearchInput placeholder="Max ₹" value={maxRent} onChangeText={setMaxRent} keyboardType="numeric" /></View>
          </View>
          <Picker selectedValue={roomType} onValueChange={setRoomType}>
            <Picker.Item label="Any room type" value="" />
            {["Single", "Double", "PG", "1BHK"].map((t) => <Picker.Item key={t} label={t} value={t} />)}
          </Picker>
          <Picker selectedValue={furnished} onValueChange={setFurnished}>
            <Picker.Item label="Furnished or not" value="" />
            <Picker.Item label="Furnished" value="Yes" />
            <Picker.Item label="Unfurnished" value="No" />
          </Picker>
        </View>
      )}
      <View style={{ marginTop: 12 }}><ErrorText>{err}</ErrorText></View>
    </View>
  );

  return (
    <FlatList
      style={{ backgroundColor: colors.bg }}
      data={loading ? [] : items}
      keyExtractor={(p) => String(p.id)}
      contentContainerStyle={{ padding: 16 }}
      keyboardShouldPersistTaps="handled"
      ListHeaderComponent={header}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={() => { setRefreshing(true); load(true); }} />}
      onEndReachedThreshold={0.5}
      onEndReached={() => more && !loading && load(false, items)}
      ListEmptyComponent={loading
        ? <ActivityIndicator style={{ marginTop: 30 }} color={colors.primary} />
        : <Empty text="No rooms match your search." />}
      renderItem={({ item }) => <PropertyCard item={item} onPress={() => navigation.navigate("Property", { id: item.id })} />}
    />
  );
}
