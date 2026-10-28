import React, { useEffect, useState } from "react";
import { Alert, KeyboardAvoidingView, Platform, ScrollView, Text, View } from "react-native";
import { LinearGradient } from "expo-linear-gradient";
import * as DocumentPicker from "expo-document-picker";
import { Picker } from "@react-native-picker/picker";
import { api, ApiError } from "../api";
import { useAuth } from "../auth";
import Icon, { IconName } from "../Icon";
import { Button, colors, ErrorText, Field, IconTile, shadow } from "../ui";

const Shell = ({ children, hero }: { children: React.ReactNode; hero?: boolean }) => (
  <LinearGradient colors={["#edf4fb", "#ffffff", "#f8fafc"]} style={{ flex: 1 }}>
    <KeyboardAvoidingView style={{ flex: 1 }} behavior={Platform.OS === "ios" ? "padding" : undefined}>
      <ScrollView contentContainerStyle={{ padding: 20, paddingTop: hero ? 64 : 24, paddingBottom: 40 }} keyboardShouldPersistTaps="handled">
        {children}
      </ScrollView>
    </KeyboardAvoidingView>
  </LinearGradient>
);

const Feature = ({ icon, title, text }: { icon: IconName; title: string; text: string }) => (
  <View style={{ flexDirection: "row", alignItems: "center", gap: 12, marginTop: 14 }}>
    <IconTile name={icon} size={44} />
    <View style={{ flex: 1 }}>
      <Text style={{ fontWeight: "800", fontSize: 15, color: colors.text }}>{title}</Text>
      <Text style={{ color: colors.muted, fontSize: 13 }}>{text}</Text>
    </View>
  </View>
);

export function LoginScreen({ navigation }: any) {
  const { signIn } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [err, setErr] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const submit = async () => {
    if (!email.trim() || !password) return setErr("Enter your email and password.");
    setBusy(true); setErr(null);
    try { await signIn(email, password); }
    catch (e) { setErr(e instanceof ApiError ? e.message : "Something went wrong."); }
    finally { setBusy(false); }
  };

  return (
    <Shell hero>
      <View style={{ flexDirection: "row", alignItems: "center", gap: 8, alignSelf: "flex-start", backgroundColor: colors.primary, paddingHorizontal: 12, paddingVertical: 6, borderRadius: 8 }}>
        <Icon name="house-heart" size={14} color="#fff" />
        <Text style={{ color: "#fff", fontWeight: "700", fontSize: 13 }}>Welcome to RoomFinder</Text>
      </View>
      <Text style={{ fontSize: 36, fontWeight: "800", color: colors.text, marginTop: 14, lineHeight: 42, letterSpacing: -0.5 }}>
        Find a place you'll <Text style={{ color: colors.primary }}>love to call home.</Text>
      </Text>
      <Text style={{ color: colors.muted, marginTop: 10, fontSize: 15 }}>
        Search comfortable rooms, PGs and rental properties that match your budget and lifestyle.
      </Text>

      <View style={[{ backgroundColor: "#fff", borderRadius: 24, padding: 22, marginTop: 28, borderWidth: 1, borderColor: colors.border }, shadow]}>
        <View style={{ alignItems: "center", marginBottom: 18 }}>
          <View style={{ width: 64, height: 64, borderRadius: 18, backgroundColor: colors.primary, alignItems: "center", justifyContent: "center", marginBottom: 12 }}>
            <Icon name="house-heart-fill" size={30} color="#fff" />
          </View>
          <Text style={{ fontSize: 26, fontWeight: "800", color: colors.text }}>Welcome Back</Text>
          <Text style={{ color: colors.muted, marginTop: 2 }}>Sign in to continue to RoomFinder</Text>
        </View>

        <Field label="Email Address" icon="envelope" placeholder="Enter your email" value={email} onChangeText={setEmail}
          autoCapitalize="none" keyboardType="email-address" autoComplete="email" />
        <Field label="Password" icon="lock" placeholder="Enter your password" value={password} onChangeText={setPassword}
          secureTextEntry autoComplete="password" onSubmitEditing={submit} />
        <ErrorText>{err}</ErrorText>
        <Button title="Login" icon="arrow-right" onPress={submit} loading={busy} />
        <Text style={{ textAlign: "center", color: colors.muted, marginVertical: 14 }}>New to RoomFinder?</Text>
        <Button title="Create an account" icon="person-plus" variant="outline" onPress={() => navigation.navigate("Register")} />
      </View>

      <View style={{ marginTop: 24 }}>
        <Feature icon="search" title="Easy Property Search" text="Find rooms according to your needs." />
        <Feature icon="shield-check" title="Trusted Listings" text="Owners are verified with a government ID." />
      </View>
    </Shell>
  );
}

export function RegisterScreen({ navigation }: any) {
  const [f, setF] = useState({ name: "", email: "", phone: "", password: "", role: "tenant", country: "" });
  const [countries, setCountries] = useState<string[]>([]);
  const [doc, setDoc] = useState<DocumentPicker.DocumentPickerAsset | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const set = (k: keyof typeof f) => (v: string) => setF((p) => ({ ...p, [k]: v }));

  useEffect(() => {
    api.countries().then((r) => {
      setCountries(r.countries);
      setF((p) => ({ ...p, country: p.country || r.countries[0] || "" }));
    }).catch(() => setErr("Could not load the country list."));
  }, []);

  const pick = async () => {
    const res = await DocumentPicker.getDocumentAsync({ type: "application/pdf", copyToCacheDirectory: true });
    if (!res.canceled) setDoc(res.assets[0]);
  };

  const submit = async () => {
    if (!f.name.trim() || !f.email.trim() || !f.password) return setErr("Fill in name, email and password.");
    if (!doc) return setErr("Attach your government ID as a PDF.");
    setBusy(true); setErr(null);
    try {
      const form = new FormData();
      Object.entries(f).forEach(([k, v]) => form.append(k, v));
      // React Native's FormData accepts { uri, name, type } for files
      form.append("government_id", { uri: doc.uri, name: doc.name, type: "application/pdf" } as any);
      await api.register(form);
      Alert.alert("Registered", "Your account is ready. Please log in.");
      navigation.goBack();
    } catch (e) {
      setErr(e instanceof ApiError ? e.message : "Something went wrong.");
    } finally { setBusy(false); }
  };

  return (
    <Shell>
      <View style={[{ backgroundColor: "#fff", borderRadius: 24, padding: 22, borderWidth: 1, borderColor: colors.border }, shadow]}>
        <View style={{ alignItems: "center", marginBottom: 18 }}>
          <View style={{ width: 64, height: 64, borderRadius: 18, backgroundColor: colors.primary, alignItems: "center", justifyContent: "center", marginBottom: 12 }}>
            <Icon name="person-plus" size={30} color="#fff" />
          </View>
          <Text style={{ fontSize: 24, fontWeight: "800", color: colors.text }}>Create your account</Text>
          <Text style={{ color: colors.muted, marginTop: 2 }}>Join RoomFinder as a tenant or owner</Text>
        </View>

        <Field label="Full name" icon="person" value={f.name} onChangeText={set("name")} placeholder="Your full name" />
        <Field label="Email Address" icon="envelope" value={f.email} onChangeText={set("email")} autoCapitalize="none" keyboardType="email-address" placeholder="Enter your email" />
        <Field label="Phone" icon="telephone" value={f.phone} onChangeText={set("phone")} keyboardType="phone-pad" placeholder="Phone number" />
        <Field label="Password" icon="lock" value={f.password} onChangeText={set("password")} secureTextEntry placeholder="Create a password" />

        <Text style={{ fontWeight: "700", fontSize: 13, marginBottom: 2 }}>I am a</Text>
        <Picker selectedValue={f.role} onValueChange={set("role")}>
          <Picker.Item label="Tenant (looking for a room)" value="tenant" />
          <Picker.Item label="Owner (listing rooms)" value="owner" />
        </Picker>
        <Text style={{ fontWeight: "700", fontSize: 13, marginBottom: 2 }}>Country</Text>
        <Picker selectedValue={f.country} onValueChange={set("country")} style={{ marginBottom: 8 }}>
          {countries.map((c) => <Picker.Item key={c} label={c} value={c} />)}
        </Picker>

        <Button title={doc ? doc.name : "Attach government ID (PDF)"} icon={doc ? "file-earmark-pdf" : "cloud-arrow-up"} variant="outline" onPress={pick} />
        <View style={{ flexDirection: "row", gap: 6, alignItems: "center", marginVertical: 10 }}>
          <Icon name="shield-lock" size={13} color={colors.muted} />
          <Text style={{ color: colors.muted, fontSize: 12, flex: 1 }}>Your ID is used only to verify your identity.</Text>
        </View>
        <ErrorText>{err}</ErrorText>
        <Button title="Register" icon="arrow-right" onPress={submit} loading={busy} />
      </View>
    </Shell>
  );
}
